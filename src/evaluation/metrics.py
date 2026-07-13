"""Context + citation-accuracy metrics (Phase 8, contracts/metric_definitions.md).

Complements src/retrieval/metrics.py (recall/hit/MRR/nDCG, aliased here as
"context recall") with the two remaining citation-coverage numbers the
context and generation layers need:

- context precision: of the chunks the runtime actually retrieved (and
  handed to the prompt), how many were relevant.
- citation accuracy: of the chunks the MODEL actually cited in its
  answer, how many were a correct source (not just a real retrieved
  chunk id — src/rag/citation.py already guarantees that part; this
  checks it was the RIGHT chunk).

Both return None rather than 0.0 when there is nothing to score against
(no citation groups, or nothing retrieved/cited) — an undefined ratio
must not silently become "0% correct" in an average.
"""

from __future__ import annotations

import re

# Category "ambiguous" trong golden set (requires_clarification=True,
# requires_refusal=False) mô tả câu hỏi thiếu thông tin để trả lời DUY NHẤT
# một cách chắc chắn — ground_truth luôn viết dưới dạng nhiều nhánh điều
# kiện. Hệ thống hiện KHÔNG có cơ chế "hỏi lại làm rõ" (không prompt nào
# trong src/promptops/templates.py hướng dẫn việc này) nên refusal_accuracy
# (vốn chỉ so requires_refusal) luôn "đúng" một cách vô nghĩa cho category
# này — cần 1 chỉ số riêng đo hệ thống có xử lý hợp lý sự mơ hồ hay không:
# hoặc hỏi lại người dùng, hoặc trả lời bao quát đủ các nhánh điều kiện,
# thay vì chốt một nhánh duy nhất như thể đó là câu trả lời chắc chắn.
# Heuristic văn bản (không tốn thêm lệnh gọi judge) — không hoàn hảo nhưng
# là con số THẬT, đo được, hơn là không đo gì.
_CLARIFYING_QUESTION_RE = re.compile(r"\?")
_SECOND_PERSON_RE = re.compile(r"\b(bạn|anh/chị|anh chị)\b", re.IGNORECASE)
_BRANCH_MARKER_RE = re.compile(
    r"\b(nếu|trường hợp|tùy|hoặc|còn nếu|khác nhau)\b", re.IGNORECASE
)
_MIN_BRANCH_MARKERS = 2


def ambiguity_handled(answer: str) -> bool:
    """True nếu answer hỏi lại người dùng để làm rõ, HOẶC bao quát nhiều
    nhánh điều kiện thay vì chốt 1 nhánh duy nhất. False = hệ thống trả lời
    như thể chỉ có 1 đáp án chắc chắn cho 1 câu hỏi vốn mơ hồ — rủi ro sai
    lệch với nhánh thật của người hỏi."""
    asked_clarifying_question = bool(
        _CLARIFYING_QUESTION_RE.search(answer) and _SECOND_PERSON_RE.search(answer)
    )
    branch_marker_count = len(_BRANCH_MARKER_RE.findall(answer))
    covered_multiple_branches = branch_marker_count >= _MIN_BRANCH_MARKERS
    return asked_clarifying_question or covered_multiple_branches


def _relevant_ids(citation_groups: list[set[str]]) -> set[str]:
    relevant: set[str] = set()
    for g in citation_groups:
        relevant |= g
    return relevant


def context_precision(
    retrieved_chunk_ids: list[str], citation_groups: list[set[str]]
) -> float | None:
    if not retrieved_chunk_ids or not citation_groups:
        return None
    relevant = _relevant_ids(citation_groups)
    if not relevant:
        return None
    hits = sum(1 for cid in retrieved_chunk_ids if cid in relevant)
    return hits / len(retrieved_chunk_ids)


def citation_accuracy(
    cited_chunk_ids: list[str], citation_groups: list[set[str]]
) -> float | None:
    if not cited_chunk_ids or not citation_groups:
        return None
    relevant = _relevant_ids(citation_groups)
    if not relevant:
        return None
    hits = sum(1 for cid in cited_chunk_ids if cid in relevant)
    return hits / len(cited_chunk_ids)
