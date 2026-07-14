"""Error clustering (Module 9 task "Implement clustering theo embedding/error
label"). Groups by (error_label, category) — deterministic, no embedding API
calls, consistent with module 8's own "judge sampling to control cost"
principle: clustering every feedback item via an embedding call would burn
Gemini quota for a backend bookkeeping feature, which isn't worth it at this
project's scale. Lexical (Jaccard token-overlap) sub-selection only decides
which sample questions to show a human reviewer, not the grouping itself."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.dataops.vietnamese_normalizer import tokenize
from src.feedback.schemas import FeedbackRecord


@dataclass
class Cluster:
    error_label: str | None
    category: str | None
    size: int
    feedback_ids: list[str]
    sample_questions: list[str] = field(default_factory=list)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster_feedback(
    records: list[FeedbackRecord],
    questions: dict[str, str] | None = None,
) -> list[Cluster]:
    """Group feedback by (error_label, category), sorted largest-first.

    `questions` (trace_id -> question text) is optional — when given, each
    cluster gets up to 3 lexically-diverse sample questions for human-review
    readability instead of just counts/trace_ids.
    """
    buckets: dict[tuple[str | None, str | None], list[FeedbackRecord]] = {}
    for r in records:
        buckets.setdefault((r.error_label, r.category), []).append(r)

    clusters: list[Cluster] = []
    for (error_label, category), items in buckets.items():
        samples: list[str] = []
        if questions:
            seen_tokens: list[set[str]] = []
            for r in items:
                q = questions.get(r.trace_id)
                if not q:
                    continue
                toks = set(tokenize(q))
                if any(_jaccard(toks, s) > 0.8 for s in seen_tokens):
                    continue
                seen_tokens.append(toks)
                samples.append(q)
                if len(samples) >= 3:
                    break
        clusters.append(
            Cluster(
                error_label=error_label,
                category=category,
                size=len(items),
                feedback_ids=[r.feedback_id for r in items],
                sample_questions=samples,
            )
        )
    clusters.sort(key=lambda c: c.size, reverse=True)
    return clusters
