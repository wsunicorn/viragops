"""Confidence heuristic (Phase 8 remediation, 2026-07-13).

`QAResponse.confidence` was `None` since Phase 5 — no ground-truth
"was this answer actually correct" labels exist to calibrate a real
probability against (the golden set has expected citations/refusal, not a
per-answer correctness score), so returning a bare float there would be
fabricated precision. This is a DETERMINISTIC HEURISTIC built only from
signals already available at response time, not a calibrated probability:
treat it as a relative ranking signal ("this answer leans more/less
trustworthy than that one"), not a P(correct).

3 inputs, all real numbers already computed by src/rag/service.py::answer():
- retrieval strength: top-1 DBSF fused score, normalized against
  `thresholds.min_score` (the calibrated pre-LLM refusal floor,
  scripts/calibrate_min_score.py) and an empirical high-anchor from the
  same calibration run (config/retrieval.yaml comment / CHECKLIST Phase 8).
- citation validity ratio: of the citations the model attempted, how many
  survived src/rag/citation.py's chunk-id validation. A response only
  reaches this function when at least 1 citation is valid (citation.py
  forces refusal when zero survive), so this only ever discounts a
  partially-valid answer, never zeroes one out here.
- transport hop: full eval (CHECKLIST Phase 8) measured Ollama local
  fallback citation-grounding quality measurably worse than primary
  Gemini (fallback group refusal_accuracy 0.457 vs primary 0.962) — a
  non-primary hop is a real, measured reason to discount, not a guess.
"""

from __future__ import annotations

SCORE_LOW_ANCHOR = 1.10  # = thresholds.min_score (config/retrieval.yaml) — điểm này đã refuse trước khi tới đây
SCORE_HIGH_ANCHOR = 2.20  # ~p85-90 vùng should_answer thật, scripts/calibrate_min_score.py (2026-07-13)
FALLBACK_PENALTY_SCORE = 0.6  # non-primary hop -> chiết khấu cố định (xem docstring, không phải đoán)

_WEIGHT_RETRIEVAL = 0.5
_WEIGHT_CITATION = 0.3
_WEIGHT_FALLBACK = 0.2


def compute_confidence(
    top_score: float, n_valid_citations: int, n_invalid_citations: int, fallback_hop: str
) -> float:
    retrieval_component = max(
        0.0, min(1.0, (top_score - SCORE_LOW_ANCHOR) / (SCORE_HIGH_ANCHOR - SCORE_LOW_ANCHOR))
    )
    attempted = n_valid_citations + n_invalid_citations
    citation_component = (n_valid_citations / attempted) if attempted else 1.0
    fallback_component = 1.0 if fallback_hop in ("primary", "n/a") else FALLBACK_PENALTY_SCORE

    return round(
        _WEIGHT_RETRIEVAL * retrieval_component
        + _WEIGHT_CITATION * citation_component
        + _WEIGHT_FALLBACK * fallback_component,
        2,
    )
