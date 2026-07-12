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
