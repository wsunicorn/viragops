"""RAG runtime orchestrator (Phase 5, Module 3).

Flow per modules/03_rag_runtime_model_gateway.md (steps not yet in scope
are owned by later phases: semantic cache -> Phase 8, LiteLLM transport
-> Phase 7, Langfuse -> Phase 10):

    validate -> ids -> normalize query -> retrieve (best config
    hybrid_dbsf_v2 from config/retrieval.yaml) -> refusal pre-check ->
    prompt (p1_grounded_v1) -> gateway -> parse/validate citations ->
    trace -> respond.

Refusal policy, two layers:
1. Pre-LLM: fewer than `thresholds.min_context_chunks` chunks retrieved
   -> refuse without spending a generation call. (`thresholds.min_score`
   is NOT enforced yet: DBSF fused scores are on a different scale than
   the cosine-like values that threshold was written for — enforcing it
   blind would over-refuse. Logged per-trace for calibration; see
   CHECKLIST Phase 5 "Chưa tốt".)
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
from src.rag.citation import parse_model_output
from src.rag.gateway_client import Gateway
from src.rag.prompt_builder import PromptProvider, build_qa_prompt
from src.rag.schemas import (
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


class RagService:
    """Loads all versioned assets once at startup; per-request work is
    embed(1 query) -> qdrant -> gateway."""

    def __init__(
        self,
        gateway: Gateway,
        qdrant_url: str,
        prompt_provider: PromptProvider,
        embed_fn=None,
    ) -> None:
        self._gateway = gateway
        self._client = QdrantClient(url=qdrant_url)
        self._traces = TraceStore()
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
        self._query_normalization: bool = rcfg.get("query_normalization", True)
        self._min_context_chunks: int = rcfg["thresholds"]["min_context_chunks"]
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

        query = normalize_for_search(req.question) if self._query_normalization else req.question

        t0 = time.perf_counter()
        dense_q = self._embed_fn(req.question)  # embedding giữ nguyên dấu câu gốc
        sparse_q = self._bm25.vectorize_query(query)
        chunks = retrieve(self._client, self._collection, self._ret_cfg, dense_q, sparse_q)
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
        }

        # --- refusal pre-check: không đủ ngữ cảnh thì không tốn 1 lần gọi LLM
        if len(chunks) < self._min_context_chunks:
            trace.update(refusal=True, refusal_stage="pre_llm", error_labels=["no_context"])
            self._traces.record(trace)
            return self._respond(
                req, request_id, trace_id,
                answer="Tài liệu hiện có không chứa thông tin liên quan để trả lời câu hỏi này.",
                citations=[], refusal=True,
                model=ModelInfo(provider="none", model="none", routing_policy=req.mode),
                usage=Usage(latency_ms=int((time.perf_counter() - t_start) * 1000)),
                chunks=chunks,
            )

        prompt = build_qa_prompt(req.question, chunks, self._prompt.template)
        gen = self._gateway.generate(tier=req.mode, prompt=prompt)
        parsed = parse_model_output(gen.text, chunks, require_citation=self._require_citation)

        # Gateway.generate() trả GenerationResult (protocol Phase 5); khi
        # transport là LiteLLM (Phase 7), gen thực ra là LiteLLMResult với
        # thêm fallback_hop/cost_usd đọc từ header proxy — MockGateway/
        # GeminiGateway (Phase 5) không có các field này, dùng getattr để
        # runtime không phụ thuộc cứng vào transport cụ thể.
        fallback_hop = getattr(gen, "fallback_hop", "n/a")
        attempted_fallbacks = getattr(gen, "attempted_fallbacks", 0)
        cost_usd = getattr(gen, "cost_usd", 0.0)
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

        return self._respond(
            req, request_id, trace_id,
            answer=parsed.answer, citations=parsed.citations, refusal=parsed.refusal,
            model=ModelInfo(provider=gen.provider, model=gen.model, routing_policy=req.mode),
            usage=Usage(
                input_tokens=gen.input_tokens,
                output_tokens=gen.output_tokens,
                cost_usd=cost_usd,
                latency_ms=int((time.perf_counter() - t_start) * 1000),
            ),
            chunks=chunks,
        )

    def _respond(self, req, request_id, trace_id, *, answer, citations, refusal,
                 model, usage, chunks) -> QAResponse | QADebugResponse:
        base = {
            "request_id": request_id,
            "trace_id": trace_id,
            "answer": answer,
            "citations": citations,
            "confidence": None,  # cần calibration thật (Phase 8) — không bịa số
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
