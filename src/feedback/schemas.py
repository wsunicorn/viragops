"""Feedback types and error taxonomy — must match sql/migrations/0002_feedback.sql's
CHECK constraints exactly (kept as plain tuples here, not an enum class, so
the DB is still the single source of truth for valid values)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FeedbackType = Literal[
    "thumbs_up", "thumbs_down", "wrong_answer", "missing_citation",
    "outdated_information", "slow_response", "unsafe_answer",
]

# 9 nhãn theo docs/system/modules/09_feedback_loop.md.
ErrorLabel = Literal[
    "retrieval_failure", "context_insufficient", "hallucination",
    "citation_error", "refusal_error", "stale_data",
    "prompt_injection", "provider_error", "cost_latency_issue",
]

Source = Literal["user", "eval_seed"]
Status = Literal["open", "reviewed", "actioned"]


@dataclass
class FeedbackRecord:
    feedback_id: str
    trace_id: str
    feedback_type: FeedbackType
    error_label: ErrorLabel
    comment: str | None = None
    rating: int | None = None
    category: str | None = None
    source: Source = "user"
    status: Status = "open"
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_note: str | None = None
    created_at: str | None = None
