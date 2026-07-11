"""Citation-coverage retrieval metrics (Phase 4, contracts/metric_definitions.md).

Relevance here is derived from expected_citations, not from exhaustive
per-chunk human judgments, so each citation is a GROUP of acceptable
chunk_ids (see citation_matcher.py — duplicate Điều numbers and
Khoản-range chunks mean several chunks can legitimately satisfy one
citation). A citation counts as covered when ANY chunk in its group is
retrieved; classic set-based recall would wrongly demand every duplicate.

- recall@k   = covered citations in top-k / total citations (per question,
               then averaged) — collapses to standard recall when every
               group has exactly one chunk.
- hit@k      = 1 if at least one citation covered in top-k.
- MRR        = 1 / rank of the first retrieved chunk that covers any
               citation.
- nDCG@k     = binary-gain DCG where a retrieved chunk earns gain 1 only
               the FIRST time it covers a not-yet-covered citation (no
               double credit for duplicates); ideal DCG places the
               min(#citations, k) gains at the top ranks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class QuestionEval:
    question_id: str
    n_citations: int
    recall_at_k: float
    hit_at_k: float
    mrr: float
    ndcg_at_k: float
    first_hit_rank: int | None  # 1-based, None if nothing covered anywhere in results


def evaluate_question(
    retrieved_chunk_ids: list[str],
    citation_groups: list[set[str]],
    k: int,
) -> QuestionEval | None:
    """Returns None when the question has no matchable citations (nothing
    to score against — excluded from aggregation rather than counted 0)."""
    groups = [g for g in citation_groups if g]
    if not groups:
        return None

    top_k = retrieved_chunk_ids[:k]

    covered_at_k = sum(1 for g in groups if any(cid in g for cid in top_k))
    recall = covered_at_k / len(groups)
    hit = 1.0 if covered_at_k > 0 else 0.0

    first_rank: int | None = None
    for rank, cid in enumerate(retrieved_chunk_ids, start=1):
        if any(cid in g for g in groups):
            first_rank = rank
            break
    mrr = 1.0 / first_rank if first_rank is not None else 0.0

    dcg = 0.0
    remaining = [set(g) for g in groups]
    for rank, cid in enumerate(top_k, start=1):
        for g in remaining:
            if cid in g:
                dcg += 1.0 / math.log2(rank + 1)
                remaining.remove(g)
                break
    ideal_hits = min(len(groups), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0

    return QuestionEval(
        question_id="",
        n_citations=len(groups),
        recall_at_k=recall,
        hit_at_k=hit,
        mrr=mrr,
        ndcg_at_k=ndcg,
        first_hit_rank=first_rank,
    )


def aggregate(evals: list[QuestionEval]) -> dict[str, float]:
    if not evals:
        return {"n_questions": 0}
    n = len(evals)
    return {
        "n_questions": n,
        "recall_at_k": sum(e.recall_at_k for e in evals) / n,
        "hit_rate": sum(e.hit_at_k for e in evals) / n,
        "mrr": sum(e.mrr for e in evals) / n,
        "ndcg_at_k": sum(e.ndcg_at_k for e in evals) / n,
    }
