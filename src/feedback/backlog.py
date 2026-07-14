"""Improvement backlog export (Module 9 task "Implement improvement backlog
export"). Pure formatting — no I/O — call site (scripts/export_improvement_backlog.py)
handles reading from FeedbackStore and writing the file."""

from __future__ import annotations

from datetime import UTC, datetime

from src.feedback.clustering import Cluster

# Nhãn lỗi -> loại sửa đề xuất, theo bảng "Mapping lỗi sang nguyên nhân" của
# docs/system/operations/observability_runbook.md.
_SUGGESTED_FIX = {
    "retrieval_failure": "retrieval",
    "context_insufficient": "retrieval",
    "hallucination": "prompt",
    "citation_error": "prompt",
    "refusal_error": "prompt",
    "stale_data": "data",
    "prompt_injection": "prompt",
    "provider_error": "routing",
    "cost_latency_issue": "routing",
}


def export_backlog(clusters: list[Cluster], min_size: int = 1) -> str:
    """Markdown improvement backlog, largest cluster first. `min_size`
    filters out singleton noise for a real production feedback stream —
    kept at 1 for eval-seeded data where every cluster is meaningful."""
    lines = [
        "# Improvement Backlog",
        "",
        f"Sinh tự động {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} từ "
        f"{sum(c.size for c in clusters)} feedback record, {len(clusters)} cluster.",
        "",
        "| Cluster | error_label | category | size | Đề xuất sửa | Câu hỏi mẫu |",
        "|---|---|---|---:|---|---|",
    ]
    ticket_no = 0
    for c in clusters:
        if c.size < min_size:
            continue
        ticket_no += 1
        fix = _SUGGESTED_FIX.get(c.error_label or "", "review")
        samples = "; ".join(c.sample_questions) if c.sample_questions else "—"
        lines.append(
            f"| TICKET-{ticket_no:03d} | {c.error_label or '—'} | {c.category or '—'} | "
            f"{c.size} | {fix} | {samples} |"
        )
    return "\n".join(lines) + "\n"
