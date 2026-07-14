"""Rule-based error classifier (Module 9 task "Implement error classifier
rule-based"). Pure function, offline, no DB/API — reads only fields already
present on the trace dict built in src/rag/service.py::answer()."""

from __future__ import annotations

from typing import Any

from src.feedback.schemas import ErrorLabel, FeedbackType


def classify_error_label(trace: dict[str, Any], feedback_type: FeedbackType) -> ErrorLabel | None:
    """Map (trace, submitted feedback_type) -> one of the 9 taxonomy labels.

    `trace` is the dict RagService.answer() records (error_labels,
    invalid_citations, refusal, fallback_hop, ...) — see runbook.md's
    "Mapping lỗi sang nguyên nhân" table for the reasoning this codifies.
    """
    if feedback_type == "thumbs_up":
        return None  # tín hiệu tích cực, không có lỗi để gán nhãn

    trace_errors: list[str] = trace.get("error_labels") or []
    fallback_hop = trace.get("fallback_hop")
    served_by_fallback = fallback_hop not in (None, "primary", "n/a")

    if feedback_type == "missing_citation":
        return "citation_error"
    if feedback_type == "outdated_information":
        return "stale_data"
    if feedback_type == "slow_response":
        return "cost_latency_issue"
    if feedback_type == "unsafe_answer":
        # Hệ thống lẽ ra phải refuse (hoặc cờ refusal bị lệch khỏi bản chất
        # câu trả lời, đúng dạng hồi quy p6 đã gặp — CHECKLIST Phase 8) —
        # cả 2 trường hợp đều là refusal_error.
        return "refusal_error"

    # wrong_answer / thumbs_down: suy luận theo trace thật, ưu tiên tín
    # hiệu cụ thể nhất trước khi rơi về mặc định.
    if trace.get("invalid_citations") or "invalid_citations_dropped" in trace_errors:
        return "citation_error"
    if trace.get("refusal"):
        return "refusal_error"  # user nói có câu trả lời đúng nhưng hệ thống đã từ chối
    if served_by_fallback:
        return "provider_error"  # model dự phòng (vd Ollama) chất lượng khác — CHECKLIST Phase 8
    if "low_score" in trace_errors or "no_context" in trace_errors:
        return "retrieval_failure"
    return "hallucination"  # mặc định: context có vẻ đủ nhưng answer sai — runbook's "context đúng"
