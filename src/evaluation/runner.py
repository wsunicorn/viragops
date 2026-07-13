"""Evaluation Engine runner (Phase 8, Module 5).

Drives the REAL RagService end-to-end per question — retrieval, prompt,
gateway, citation parsing, refusal policy are all production code paths
(src/rag/service.py), not a re-implementation that could silently drift.
This means every scored question costs one real generation call, plus one
real judge call for non-refusal answers.

Relevance ground truth is recomputed per question via
src/retrieval/citation_matcher.py (same approach as Phase 4's
scripts/run_experiment.py) rather than read from golden_set.jsonl's
flattened `relevant_chunks` field, because that field merges all citation
groups into one list and loses the per-citation grouping recall/nDCG need.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.evaluation import metrics as em
from src.evaluation.judge import GeminiJudge
from src.rag.gateway_client import GatewayError
from src.rag.schemas import QARequest
from src.rag.service import RagService
from src.retrieval import metrics as rm
from src.retrieval.citation_matcher import match_question

JUDGE_CALL_DELAY = 6.5  # giây — cùng nhịp RERANK_CALL_DELAY (Phase 4), tránh 429 tier judge


@dataclass
class QuestionResult:
    question_id: str
    category: str
    requires_refusal: bool
    requires_clarification: bool
    got_refusal: bool
    refusal_correct: bool
    retrieval_eval: rm.QuestionEval | None
    context_precision: float | None
    citation_accuracy: float | None
    judge: dict[str, Any] | None
    latency_ms: int
    cost_usd: float
    fallback_hop: str
    error_labels: list[str] = field(default_factory=list)
    trace_id: str = ""
    question: str = ""
    judge2: dict[str, Any] | None = None
    ambiguity_handled: bool | None = None


def _run_judge(
    judge: GeminiJudge, question: str, answer: str, context_text: str, ground_truth: str
) -> dict[str, Any]:
    try:
        score = judge.score(question, answer, context_text, ground_truth)
        result = {
            "faithfulness": score.faithfulness,
            "answer_relevance": score.answer_relevance,
            "context_relevance": score.context_relevance,
            "hallucination": score.hallucination,
        }
        if not score.from_cache:
            time.sleep(JUDGE_CALL_DELAY)
        return result
    except GatewayError as exc:
        return {"error": str(exc)[:200]}


def run_question(
    service: RagService,
    judge: GeminiJudge | None,
    item: dict,
    chunks_by_doc: dict,
    chunk_text_by_id: dict[str, str],
    eval_k: int = 5,
    judge2: GeminiJudge | None = None,
) -> QuestionResult:
    req = QARequest(question=item["question"], mode="balanced", debug=True)
    resp = service.answer(req)
    trace = service.get_trace(resp.trace_id) or {}

    groups = [set(m.chunk_ids) for m in match_question(item, chunks_by_doc)]
    groups = [g for g in groups if g]

    retrieved_ids = [c["chunk_id"] for c in trace.get("retrieved", [])]
    ret_eval: rm.QuestionEval | None = None
    if groups:
        ret_eval = rm.evaluate_question(retrieved_ids, groups, k=eval_k)
        if ret_eval is not None:
            ret_eval.question_id = item["id"]

    ctx_precision = em.context_precision(retrieved_ids, groups)

    cited_ids = [c.chunk_id for c in resp.citations]
    cit_acc = em.citation_accuracy(cited_ids, groups) if not resp.refusal else None

    amb_handled: bool | None = None
    if item["category"] == "ambiguous" and not resp.refusal:
        amb_handled = em.ambiguity_handled(resp.answer)

    judge_result: dict[str, Any] | None = None
    judge2_result: dict[str, Any] | None = None
    if (judge is not None or judge2 is not None) and not resp.refusal:
        context_text = "\n\n".join(chunk_text_by_id.get(cid, "") for cid in retrieved_ids)
        ground_truth = item.get("ground_truth", "")
        if judge is not None:
            judge_result = _run_judge(judge, item["question"], resp.answer, context_text, ground_truth)
        if judge2 is not None:
            judge2_result = _run_judge(judge2, item["question"], resp.answer, context_text, ground_truth)

    return QuestionResult(
        question_id=item["id"],
        category=item["category"],
        requires_refusal=item["requires_refusal"],
        requires_clarification=item.get("requires_clarification", False),
        got_refusal=resp.refusal,
        refusal_correct=resp.refusal == item["requires_refusal"],
        retrieval_eval=ret_eval,
        context_precision=ctx_precision,
        citation_accuracy=cit_acc,
        judge=judge_result,
        latency_ms=trace.get("generation_ms") or 0,
        cost_usd=trace.get("cost_usd") or 0.0,
        fallback_hop=trace.get("fallback_hop", "n/a"),
        error_labels=trace.get("error_labels") or [],
        trace_id=resp.trace_id,
        question=item["question"],
        judge2=judge2_result,
        ambiguity_handled=amb_handled,
    )


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    idx = max(0, int(len(sorted_values) * pct) - 1)
    return round(sorted_values[idx], 1)


_NUMERIC_CRITERIA = ("faithfulness", "answer_relevance", "context_relevance")


def inter_judge_agreement(results: list[QuestionResult]) -> dict[str, Any] | None:
    """So sánh judge chính (tier=judge, gemini-3-flash-preview) với judge phụ
    (tier=cheap, gemini-3.1-flash-lite) trên CÙNG (question, answer, context)
    — 2 model Gemini khác nhau (cùng provider, chưa có key OpenAI/Anthropic,
    xem config/model_gateway.yaml), không phải giả lập đa dạng judge. Mục
    đích: đo judge rẻ có đáng tin để thay judge đắt hay không, không phải
    "đúng tuyệt đối" (không có judge nào là ground truth)."""
    pairs = [
        (r.judge, r.judge2) for r in results
        if r.judge and "error" not in r.judge and r.judge2 and "error" not in r.judge2
    ]
    if not pairs:
        return None

    agreement: dict[str, Any] = {"n_pairs": len(pairs)}
    for crit in _NUMERIC_CRITERIA:
        diffs = [abs(j1[crit] - j2[crit]) for j1, j2 in pairs]
        agreement[f"{crit}_mean_abs_diff"] = round(_mean(diffs), 3)
        agreement[f"{crit}_exact_match_rate"] = round(
            sum(1 for d in diffs if d == 0.0) / len(diffs), 3
        )
    hallu_matches = sum(1 for j1, j2 in pairs if j1["hallucination"] == j2["hallucination"])
    agreement["hallucination_agreement_rate"] = round(hallu_matches / len(pairs), 3)
    return agreement


def aggregate(results: list[QuestionResult], eval_k: int = 5) -> dict[str, Any]:
    n = len(results)
    if n == 0:
        return {"n_questions": 0}

    ret_evals = [r.retrieval_eval for r in results if r.retrieval_eval is not None]
    retrieval_agg = rm.aggregate(ret_evals) if ret_evals else {"n_questions": 0}

    ctx_precisions = [r.context_precision for r in results if r.context_precision is not None]
    judged = [r.judge for r in results if r.judge and "error" not in r.judge]
    cit_accs = [r.citation_accuracy for r in results if r.citation_accuracy is not None]
    amb_handled = [r.ambiguity_handled for r in results if r.ambiguity_handled is not None]

    latencies = sorted(r.latency_ms for r in results if r.latency_ms)
    fallback_used = [
        r for r in results if r.fallback_hop not in ("primary", "n/a", "unknown", None)
    ]

    return {
        "n_questions": n,
        "eval_k": eval_k,
        "retrieval": retrieval_agg,
        "context_precision": _mean(ctx_precisions),
        "context_recall": retrieval_agg.get("recall_at_k"),  # alias — same citation-coverage definition
        "context_relevance": _mean([j["context_relevance"] for j in judged]),
        "faithfulness": _mean([j["faithfulness"] for j in judged]),
        "answer_relevance": _mean([j["answer_relevance"] for j in judged]),
        "hallucination_rate": _mean([1.0 if j["hallucination"] else 0.0 for j in judged]),
        "citation_accuracy": _mean(cit_accs),
        "refusal_accuracy": sum(1 for r in results if r.refusal_correct) / n,
        "n_judged": len(judged),
        "n_judge_errors": sum(1 for r in results if r.judge and "error" in r.judge),
        "p50_latency_ms": _percentile(latencies, 0.5),
        "p95_latency_ms": _percentile(latencies, 0.95),
        "avg_cost_usd": _mean([r.cost_usd for r in results]) or 0.0,
        "error_rate": sum(1 for r in results if r.error_labels) / n,
        "fallback_rate": len(fallback_used) / n,
        # Semantic cache chưa implement trong RAG runtime (ngoài scope Phase
        # 8) -> không có số thật để báo, không bịa 0.0 như thể đã đo được.
        "cache_hit_rate": None,
        "inter_judge_agreement": inter_judge_agreement(results),
        # Chỉ có giá trị khi n>0 (chỉ category="ambiguous" mới gán
        # ambiguity_handled) — None khi không câu nào thuộc category này
        # trong tập results, không bịa 0.0.
        "ambiguity_handling_rate": _mean([1.0 if h else 0.0 for h in amb_handled]),
        "n_ambiguity_scored": len(amb_handled),
    }
