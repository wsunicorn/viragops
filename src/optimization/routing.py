"""Model-tier routing by query complexity + dynamic top-k cutoff (Module 8).

Both are pure functions — no I/O, no model calls — so they're cheap to
call on every request and trivially unit-testable.
"""

from __future__ import annotations

import re
from typing import Literal

from src.dataops.vietnamese_normalizer import normalize_for_search

Complexity = Literal["simple", "medium", "hard"]

# Cùng nhóm liên từ nối vế đã dùng để phát hiện câu hỏi multi-hop trong
# thí nghiệm per-hop retrieval (CHECKLIST item 9, đã revert vì không cải
# thiện RETRIEVAL) — ở đây dùng cho một mục đích khác và rủi ro thấp hơn
# nhiều: chỉ chọn TIER model, không đổi chiến lược retrieval.
_MULTI_PART_RE = re.compile(
    r"\b(và|vừa|cũng như|đồng thời|hoặc|hay|nhưng|nếu.*thì)\b", re.IGNORECASE
)
_SIMPLE_MAX_CHARS = 60


def classify_complexity(question: str) -> Complexity:
    """Rule-based: short single-clause question -> simple; a question with
    a multi-part connector -> hard (more likely multi-hop, worth the
    stronger/slower model); everything else -> medium."""
    normalized = normalize_for_search(question)
    if _MULTI_PART_RE.search(normalized):
        return "hard"
    if len(question) <= _SIMPLE_MAX_CHARS:
        return "simple"
    return "medium"


_TIER_BY_COMPLEXITY: dict[Complexity, str] = {
    "simple": "cheap",
    "medium": "balanced",
    "hard": "strong",
}


def resolve_tier(question: str) -> str:
    """question -> a real model_gateway.yaml tier name (cheap/balanced/strong)."""
    return _TIER_BY_COMPLEXITY[classify_complexity(question)]


def dynamic_top_k(scores: list[float], min_score: float, base_k: int = 5, max_k: int = 10) -> int:
    """How many of the (over-fetched, up to max_k) retrieved chunks to
    actually pass into the prompt.

    Confident top score (comfortably above min_score) -> fewer chunks
    (less noise for the model to over-cite from — CHECKLIST Phase 8 found
    MORE chunks measurably HURT citation accuracy). Borderline top score
    (close to min_score) -> more chunks, since retrieval itself is less
    sure and the extra context may be needed to actually answer.
    """
    if not scores:
        return base_k
    top = scores[0]
    margin = top - min_score
    if margin <= 0.3:  # borderline retrieval
        return min(max_k, base_k + 3)
    if margin >= 1.0:  # confidently above threshold
        return max(1, base_k - 2)
    return base_k
