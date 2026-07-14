"""RAG runtime orchestrator (Phase 5, Module 3).

Flow per modules/03_rag_runtime_model_gateway.md (steps not yet in scope
are owned by later phases: semantic cache -> Phase 8, LiteLLM transport
-> Phase 7, Langfuse -> Phase 10):

    validate -> ids -> normalize query -> retrieve (best config
    hybrid_dbsf_v2 from config/retrieval.yaml) -> refusal pre-check ->
    prompt (p1_grounded_v1) -> gateway -> parse/validate citations ->
    trace -> respond.

Multi-hop per-hop retrieval — TRIED AND REVERTED (2026-07-14, CHECKLIST
item 9), negative result with real value, same pattern as the
top_k_after 5->10 experiment (CHECKLIST Phase 8): query decomposition +
per-hop retrieval + merge was hypothesized to fix multi_hop's Citation
Accuracy gap by giving each sub-question its own retrieval pass. Measured
on the same 30 real multi_hop questions, same prompt, 3 controlled runs:
single-query baseline (Recall@5=0.856, Citation Accuracy=0.684) beat BOTH
a raw-score-merge version (0.767 / 0.606) AND a round-robin-merge version
that fixed a real DBSF-score-not-comparable-across-queries bug in the
first attempt (0.739 / 0.650) — decomposition never caught up to simply
sending the whole question to the existing hybrid DBSF retrieval, which
already handles multi-clause questions better than 2-3 independently
retrieved and re-merged sub-queries. Full analysis: CHECKLIST Phase 8
"Sửa citation accuracy multi-hop/ambiguous". The multi_hop citation gap
remains open; per-hop retrieval is not the fix.

Refusal policy, two layers:
1. Pre-LLM: fewer than `thresholds.min_context_chunks` chunks retrieved,
   OR top-1 DBSF fused score below `thresholds.min_score` -> refuse
   without spending a generation call. `min_score` was calibrated
   2026-07-13 from 875 real traces (scripts/calibrate_min_score.py,
   data/traces/traces.jsonl) instead of the earlier guessed 0.15 (written
   for a cosine-like scale, never matched DBSF's actual range ~0.9-2.7):
   should_answer/should_refuse top-1 scores overlap heavily (medians 2.02
   vs 1.63) so this threshold is a weak, secondary signal — it is set at
   1.10 specifically because in the calibration sample it wrongly refused
   ZERO of 720 real answerable questions while still catching a handful
   of degenerate-retrieval cases (2/147 should_refuse below it at that
   level; the real adversarial/out_of_scope refusal work is done by the
   LLM itself in the post-LLM layer below, not by this score).
2. Post-LLM: the model may declare refusal, and an answer whose every
   citation failed validation is downgraded to refusal (citation.py).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml
from qdrant_client import QdrantClient

from src.dataops import embedder
from src.dataops.sparse_bm25 import BM25Sparse
from src.dataops.vietnamese_normalizer import normalize_for_search
from src.observability import metrics as obs_metrics
from src.observability import tracing as obs_tracing
from src.optimization import routing as opt_routing
from src.optimization.compression import compress_chunks
from src.optimization.semantic_cache import SemanticCache
from src.rag.citation import parse_model_output
from src.rag.confidence import compute_confidence
from src.rag.gateway_client import Gateway
from src.rag.prompt_builder import PromptProvider, build_qa_prompt
from src.rag.schemas import (
    Citation,
    ModelInfo,
    QADebugResponse,
    QARequest,
    QAResponse,
    RetrievedChunkDebug,
    Usage,
)
from src.rag.trace_store import TraceStore, new_id
from src.retrieval.retriever import RetrievalConfig, retrieve

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
RETRIEVAL_CONFIG_PATH = PROJECT_ROOT / "config" / "retrieval.yaml"
INGEST_CONFIG_PATH = PROJECT_ROOT / "config" / "ingest.yaml"
PROMPTS_CONFIG_PATH = PROJECT_ROOT / "config" / "prompts.yaml"
GATEWAY_CONFIG_PATH = PROJECT_ROOT / "config" / "model_gateway.yaml"
OPTIMIZATION_CONFIG_PATH = PROJECT_ROOT / "config" / "optimization.yaml"


class RagService:
    """Loads all versioned assets once at startup; per-request work is
    embed(1 query) -> qdrant -> gateway."""

    def __init__(
        self,
        gateway: Gateway,
        qdrant_url: str,
        prompt_provider: PromptProvider,
        embed_fn=None,
        langfuse=None,
        enable_semantic_cache: bool = False,
        enable_context_compression: bool = False,
        enable_dynamic_top_k: bool = False,
    ) -> None:
        self._gateway = gateway
        self._client = QdrantClient(url=qdrant_url)
        self._traces = TraceStore()
        # Phase 10: Langfuse client injectable (None = tracing tắt, mọi
        # test/script hiện có không cần đổi gì) — xem src/observability/tracing.py.
        self._langfuse = langfuse
        # Phase 6: prompt lấy từ registry (Module 4), KHÔNG hard-code —
        # provider injectable để test không cần Postgres.
        self._prompt = prompt_provider.get_active()
        # embed_fn injectable: integration tests thay bằng vector giả để
        # không tốn quota Gemini cho mỗi lần chạy test.
        self._embed_fn = embed_fn or self._embed_query

        rcfg = yaml.safe_load(RETRIEVAL_CONFIG_PATH.read_text(encoding="utf-8"))
        icfg = yaml.safe_load(INGEST_CONFIG_PATH.read_text(encoding="utf-8"))
        pcfg = yaml.safe_load(PROMPTS_CONFIG_PATH.read_text(encoding="utf-8"))

        self.retrieval_config_id: str = rcfg["retrieval_config_id"]
        self.data_version: str | None = rcfg.get("data_version")
        self.index_version: str | None = rcfg.get("index_version")
        obs_metrics.set_data_version_info(self.data_version)
        self._query_normalization: bool = rcfg.get("query_normalization", True)
        self._min_context_chunks: int = rcfg["thresholds"]["min_context_chunks"]
        self._min_score: float = rcfg["thresholds"]["min_score"]
        self._require_citation: bool = pcfg["policy"]["require_citation"]

        fusion = rcfg["retrieval"]["fusion"]["method"]
        # Public (không phải chỉ _ret_cfg.limit nội bộ) vì Phase 8 eval engine
        # cần biết đúng con số này để tính Recall@k khớp với những gì runtime
        # THẬT SỰ đưa cho model — hardcode k=5 riêng ở tầng eval sẽ lệch nếu
        # con số này đổi (đã xảy ra thật: 5->10, xem CHECKLIST Phase 8).
        self.context_limit: int = rcfg["reranker"]["top_k_after"]
        self._ret_cfg = RetrievalConfig(
            config_id=self.retrieval_config_id,
            mode=f"hybrid_{fusion}" if rcfg["retrieval"]["type"] == "hybrid" else rcfg["retrieval"]["type"],
            top_k_before=rcfg["retrieval"]["dense"]["top_k"],
            limit=self.context_limit,
        )

        self._collection = (
            f"{icfg['qdrant']['collection_prefix']}_{self.index_version}"
        )
        self._dense_cfg = icfg["embedding"]["dense"]

        state_path = CHUNKS_DIR / f"bm25_state_structure_aware_{self.data_version}.json"
        if not state_path.exists():
            state_path = CHUNKS_DIR / f"bm25_state_{self.data_version}.json"
        self._bm25 = BM25Sparse.from_state(json.loads(state_path.read_text(encoding="utf-8")))

        gwcfg = yaml.safe_load(GATEWAY_CONFIG_PATH.read_text(encoding="utf-8"))
        # Budget warning (Phase 7): tổng cost_usd trong tiến trình server so
        # với budget.daily_usd. Reset về 0 khi restart — CHƯA phải cost
        # tracking bền vững qua nhiều lần chạy (Phase 10/Langfuse). Free
        # tier Gemini cost=0 thật, nhưng litellm vẫn tính "giá niêm yết" nếu
        # hết free tier — cảnh báo này bắt được ngày mai cost thật phát sinh.
        self._daily_budget_usd: float = gwcfg.get("budget", {}).get("daily_usd", 0.0)
        self._cumulative_cost_usd: float = 0.0

        # Phase 11 (Module 8): mọi optimization feature mặc định TẮT
        # (constructor flag = False) — bật sau khi đã đo qua O1-O8
        # experiment, cùng nguyên tắc "đo trước khi đổi default production"
        # đã áp dụng cho reranker (Phase 4) và top_k_after (Phase 8).
        ocfg = yaml.safe_load(OPTIMIZATION_CONFIG_PATH.read_text(encoding="utf-8"))
        self._budget_hard_block: bool = ocfg["budget"]["hard_block"]
        self._compression_max_chars: int = ocfg["context_compression"]["max_chars_per_chunk"]
        self._dynamic_top_k_base: int = ocfg["dynamic_top_k"]["base_k"]
        self._dynamic_top_k_max: int = ocfg["dynamic_top_k"]["max_k"]
        self._enable_context_compression = enable_context_compression
        self._enable_dynamic_top_k = enable_dynamic_top_k
        self._semantic_cache: SemanticCache | None = None
        if enable_semantic_cache:
            self._semantic_cache = SemanticCache(
                self._client,
                index_version=self.index_version or "unversioned",
                vector_size=self._dense_cfg["output_dimensionality"],
                similarity_threshold=ocfg["semantic_cache"]["similarity_threshold"],
            )

    # --- per-request pipeline -------------------------------------------

    def _embed_query(self, question: str) -> list[float]:
        return embedder.embed_batch(
            [question],
            model=self._dense_cfg["model_ref"],
            task_type=self._dense_cfg["task_type_query"],
            output_dimensionality=self._dense_cfg["output_dimensionality"],
        )[0]

    def answer(self, req: QARequest) -> QAResponse | QADebugResponse:
        request_id = new_id("req")
        trace_id = new_id("trace")
        t_start = time.perf_counter()

        lf_span = obs_tracing.start_qa_span(self._langfuse, trace_id, req.question)

        query = normalize_for_search(req.question) if self._query_normalization else req.question
        # Phase 11: "auto" resolves a real tier via query-complexity rules
        # (src/optimization/routing.py) — an explicit mode is always
        # respected as-is, "auto" is opt-in per request.
        tier = opt_routing.resolve_tier(req.question) if req.mode == "auto" else req.mode

        t0 = time.perf_counter()
        dense_q = self._embed_fn(req.question)  # embedding giữ nguyên dấu câu gốc

        if self._semantic_cache is not None:
            cached = self._semantic_cache.lookup(dense_q, self._prompt.version)
            if cached is not None:
                return self._respond_from_cache(req, request_id, trace_id, tier, cached, lf_span, t_start)

        sparse_q = self._bm25.vectorize_query(query)
        # Dynamic top-k (Phase 11): over-fetch to max_k, decide the real
        # cut client-side from the returned scores — avoids a 2nd Qdrant
        # round-trip (retriever.py's fetch_limit already supports this).
        fetch_limit = self._dynamic_top_k_max if self._enable_dynamic_top_k else None
        chunks = retrieve(self._client, self._collection, self._ret_cfg, dense_q, sparse_q, fetch_limit=fetch_limit)
        if self._enable_dynamic_top_k:
            k = opt_routing.dynamic_top_k(
                [c["score"] for c in chunks], self._min_score,
                base_k=self._dynamic_top_k_base, max_k=self._dynamic_top_k_max,
            )
            chunks = chunks[:k]
        retrieval_ms = int((time.perf_counter() - t0) * 1000)

        trace: dict[str, Any] = {
            "trace_id": trace_id,
            "request_id": request_id,
            "session_id": req.session_id,
            "question": req.question,
            "normalized_query": query,
            "data_version": self.data_version,
            "index_version": self.index_version,
            "retrieval_config_id": self.retrieval_config_id,
            "prompt_version": self._prompt.version,
            "retrieval_ms": retrieval_ms,
            "retrieved": [
                {"chunk_id": c["chunk_id"], "score": round(c["score"], 4)} for c in chunks
            ],
            "cache_result": "miss" if self._semantic_cache is not None else None,
        }

        # --- refusal pre-check: không đủ ngữ cảnh (số lượng HOẶC score đỉnh
        # quá thấp, xem docstring đầu file) thì không tốn 1 lần gọi LLM
        top_score = max((c["score"] for c in chunks), default=0.0)
        if len(chunks) < self._min_context_chunks or top_score < self._min_score:
            error_label = "no_context" if len(chunks) < self._min_context_chunks else "low_score"
            pre_llm_answer = "Tài liệu hiện có không chứa thông tin liên quan để trả lời câu hỏi này."
            total_latency_ms = int((time.perf_counter() - t_start) * 1000)
            trace.update(
                refusal=True, refusal_stage="pre_llm", error_labels=[error_label],
                answer=pre_llm_answer,
            )
            self._traces.record(trace)
            obs_tracing.end_qa_span(lf_span, trace, confidence=None)
            obs_metrics.record_request(trace, total_latency_ms)
            if self._semantic_cache is not None:
                self._semantic_cache.store(dense_q, self._prompt.version, {
                    "answer": pre_llm_answer, "citations": [], "refusal": True,
                    "model_provider": "none", "model_name": "none", "confidence": None,
                })
            return self._respond(
                req, request_id, trace_id,
                answer=pre_llm_answer,
                citations=[], refusal=True,
                model=ModelInfo(provider="none", model="none", routing_policy=tier),
                usage=Usage(latency_ms=total_latency_ms),
                chunks=chunks,
            )

        # Budget hard-block (Phase 11): nếu đã vượt daily_usd TỪ CÁC request
        # trước đó và ocfg.budget.hard_block=true, hạ tier xuống "cheap" cho
        # request NÀY thay vì chỉ cảnh báo (hành vi cũ vẫn giữ khi false —
        # xem budget_warning bên dưới, tính SAU khi có cost_usd thật).
        over_budget_before = self._daily_budget_usd > 0 and self._cumulative_cost_usd >= self._daily_budget_usd
        budget_downgraded = self._budget_hard_block and over_budget_before and tier != "cheap"
        if budget_downgraded:
            tier = "cheap"

        chunks_for_prompt = (
            compress_chunks(chunks, req.question, max_chars=self._compression_max_chars)
            if self._enable_context_compression
            else chunks
        )
        prompt = build_qa_prompt(req.question, chunks_for_prompt, self._prompt.template)
        lf_gen = obs_tracing.start_generation_span(lf_span, prompt, tier)
        gen = self._gateway.generate(tier=tier, prompt=prompt)
        parsed = parse_model_output(gen.text, chunks, require_citation=self._require_citation)

        # Gateway.generate() trả GenerationResult (protocol Phase 5); khi
        # transport là LiteLLM (Phase 7), gen thực ra là LiteLLMResult với
        # thêm fallback_hop/cost_usd đọc từ header proxy — MockGateway/
        # GeminiGateway (Phase 5) không có các field này, dùng getattr để
        # runtime không phụ thuộc cứng vào transport cụ thể.
        fallback_hop = getattr(gen, "fallback_hop", "n/a")
        attempted_fallbacks = getattr(gen, "attempted_fallbacks", 0)
        cost_usd = getattr(gen, "cost_usd", 0.0)
        obs_tracing.end_generation_span(lf_gen, gen, cost_usd)
        self._cumulative_cost_usd += cost_usd
        budget_warning = (
            self._daily_budget_usd > 0 and self._cumulative_cost_usd > self._daily_budget_usd
        )

        error_labels = []
        if parsed.parse_error:
            error_labels.append(parsed.parse_error)
        if parsed.invalid_citations:
            error_labels.append("invalid_citations_dropped")
        if fallback_hop not in ("primary", "n/a"):
            error_labels.append(f"served_by_fallback:{fallback_hop}")
        if budget_warning:
            error_labels.append("budget_warning")
        if budget_downgraded:
            error_labels.append("budget_downgrade")

        trace.update(
            model_provider=gen.provider,
            model_name=gen.model,
            fallback_hop=fallback_hop,
            attempted_fallbacks=attempted_fallbacks,
            cost_usd=cost_usd,
            cumulative_cost_usd=round(self._cumulative_cost_usd, 6),
            input_tokens=gen.input_tokens,
            output_tokens=gen.output_tokens,
            generation_ms=gen.latency_ms,
            refusal=parsed.refusal,
            refusal_stage="post_llm" if parsed.refusal else None,
            citations=[c.chunk_id for c in parsed.citations],
            invalid_citations=parsed.invalid_citations,
            error_labels=error_labels,
            answer=parsed.answer,
        )
        self._traces.record(trace)

        confidence = (
            None
            if parsed.refusal
            else compute_confidence(
                top_score=top_score,
                n_valid_citations=len(parsed.citations),
                n_invalid_citations=len(parsed.invalid_citations),
                fallback_hop=fallback_hop,
            )
        )

        obs_tracing.end_qa_span(lf_span, trace, confidence)
        total_latency_ms = int((time.perf_counter() - t_start) * 1000)
        obs_metrics.record_request(trace, total_latency_ms)

        if self._semantic_cache is not None:
            self._semantic_cache.store(dense_q, self._prompt.version, {
                "answer": parsed.answer,
                "citations": [c.model_dump() for c in parsed.citations],
                "refusal": parsed.refusal,
                "model_provider": gen.provider, "model_name": gen.model,
                "confidence": confidence,
            })

        return self._respond(
            req, request_id, trace_id,
            answer=parsed.answer, citations=parsed.citations, refusal=parsed.refusal,
            model=ModelInfo(provider=gen.provider, model=gen.model, routing_policy=tier),
            usage=Usage(
                input_tokens=gen.input_tokens,
                output_tokens=gen.output_tokens,
                cost_usd=cost_usd,
                latency_ms=total_latency_ms,
            ),
            chunks=chunks,
            confidence=confidence,
        )

    def _respond_from_cache(
        self, req, request_id, trace_id, tier, cached, lf_span, t_start
    ) -> QAResponse | QADebugResponse:
        """Cache hit (Phase 11): skip retrieval AND generation entirely."""
        total_latency_ms = int((time.perf_counter() - t_start) * 1000)
        trace: dict[str, Any] = {
            "trace_id": trace_id,
            "request_id": request_id,
            "session_id": req.session_id,
            "question": req.question,
            "normalized_query": req.question,
            "data_version": self.data_version,
            "index_version": self.index_version,
            "retrieval_config_id": self.retrieval_config_id,
            "prompt_version": self._prompt.version,
            "retrieval_ms": 0,
            "retrieved": [],
            "cache_result": "hit",
            "model_provider": cached["model_provider"],
            "model_name": cached["model_name"],
            "fallback_hop": "cache",
            "attempted_fallbacks": 0,
            "cost_usd": 0.0,
            "cumulative_cost_usd": round(self._cumulative_cost_usd, 6),
            "input_tokens": 0,
            "output_tokens": 0,
            "generation_ms": 0,
            "refusal": cached["refusal"],
            "refusal_stage": "cache" if cached["refusal"] else None,
            "citations": [c["chunk_id"] for c in cached["citations"]],
            "invalid_citations": [],
            "error_labels": [],
            "answer": cached["answer"],
        }
        self._traces.record(trace)
        obs_tracing.end_qa_span(lf_span, trace, cached.get("confidence"))
        obs_metrics.record_request(trace, total_latency_ms)
        return self._respond(
            req, request_id, trace_id,
            answer=cached["answer"],
            citations=[Citation(**c) for c in cached["citations"]],
            refusal=cached["refusal"],
            model=ModelInfo(
                provider=cached["model_provider"], model=cached["model_name"], routing_policy=f"cache:{tier}"
            ),
            usage=Usage(latency_ms=total_latency_ms),
            chunks=[],
            confidence=cached.get("confidence"),
        )

    def _respond(self, req, request_id, trace_id, *, answer, citations, refusal,
                 model, usage, chunks, confidence=None) -> QAResponse | QADebugResponse:
        base = {
            "request_id": request_id,
            "trace_id": trace_id,
            "answer": answer,
            "citations": citations,
            # Heuristic có căn cứ (retrieval score + citation validity +
            # fallback hop), KHÔNG phải xác suất calibrate qua ground-truth
            # correctness (chưa có nhãn đó) — xem src/rag/confidence.py.
            # None cho câu refusal (không có "độ tin cậy của việc từ chối").
            "confidence": confidence,
            "refusal": refusal,
            "model": model,
            "usage": usage,
        }
        if not req.debug:
            return QAResponse(**base)
        return QADebugResponse(
            **base,
            retrieved_chunks=[
                RetrievedChunkDebug(
                    chunk_id=c["chunk_id"],
                    score=c["score"],
                    section=c.get("section"),
                    document_id=c["document_id"],
                    text_preview=c["text"][:200],
                )
                for c in chunks
            ],
            prompt_version=self._prompt.version,
            retrieval_config_id=self.retrieval_config_id,
            data_version=self.data_version,
            index_version=self.index_version,
        )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        return self._traces.get(trace_id)

    def flush_traces(self) -> None:
        """Gọi ở cuối 1 tiến trình ngắn hạn (script eval/demo traffic) —
        API server chạy dài không cần, Langfuse SDK tự flush nền định kỳ."""
        obs_tracing.flush(self._langfuse)
