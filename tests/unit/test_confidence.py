"""Unit test cho confidence heuristic (Phase 8 remediation, 2026-07-13) —
thuần hàm số, không cần service/Qdrant/gateway."""

from __future__ import annotations

from src.rag.confidence import (
    SCORE_HIGH_ANCHOR,
    SCORE_LOW_ANCHOR,
    compute_confidence,
)


def test_confidence_at_low_score_anchor_and_no_citations_is_low():
    c = compute_confidence(
        top_score=SCORE_LOW_ANCHOR, n_valid_citations=1, n_invalid_citations=1, fallback_hop="primary"
    )
    # retrieval_component=0, citation_component=0.5, fallback_component=1.0
    assert c == round(0.3 * 0.5 + 0.2 * 1.0, 2)


def test_confidence_at_high_score_all_valid_primary_is_max():
    c = compute_confidence(
        top_score=SCORE_HIGH_ANCHOR, n_valid_citations=2, n_invalid_citations=0, fallback_hop="primary"
    )
    assert c == 1.0


def test_confidence_no_citations_attempted_treated_as_full_citation_component():
    c = compute_confidence(
        top_score=SCORE_HIGH_ANCHOR, n_valid_citations=0, n_invalid_citations=0, fallback_hop="primary"
    )
    assert c == 1.0


def test_confidence_fallback_hop_discounts():
    primary = compute_confidence(
        top_score=SCORE_HIGH_ANCHOR, n_valid_citations=1, n_invalid_citations=0, fallback_hop="primary"
    )
    fallback = compute_confidence(
        top_score=SCORE_HIGH_ANCHOR, n_valid_citations=1, n_invalid_citations=0, fallback_hop="local"
    )
    assert fallback < primary


def test_confidence_score_below_low_anchor_clamped_not_negative():
    c = compute_confidence(
        top_score=0.0, n_valid_citations=1, n_invalid_citations=0, fallback_hop="primary"
    )
    assert c >= 0.0


def test_confidence_score_above_high_anchor_clamped_not_over_one():
    c = compute_confidence(
        top_score=99.0, n_valid_citations=1, n_invalid_citations=0, fallback_hop="primary"
    )
    assert c == 1.0
