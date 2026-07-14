"""Unit test cho rule-based error classifier (Phase 11, Module 9)."""

from __future__ import annotations

from src.feedback.classifier import classify_error_label


def _trace(**overrides) -> dict:
    base = {
        "error_labels": [],
        "invalid_citations": [],
        "refusal": False,
        "fallback_hop": "primary",
    }
    base.update(overrides)
    return base


def test_thumbs_up_has_no_error_label():
    assert classify_error_label(_trace(), "thumbs_up") is None


def test_missing_citation_always_citation_error():
    assert classify_error_label(_trace(), "missing_citation") == "citation_error"


def test_outdated_information_maps_to_stale_data():
    assert classify_error_label(_trace(), "outdated_information") == "stale_data"


def test_slow_response_maps_to_cost_latency_issue():
    assert classify_error_label(_trace(), "slow_response") == "cost_latency_issue"


def test_unsafe_answer_maps_to_refusal_error():
    assert classify_error_label(_trace(refusal=False), "unsafe_answer") == "refusal_error"


def test_wrong_answer_with_invalid_citations_is_citation_error():
    trace = _trace(invalid_citations=["chunk_bia_dat"])
    assert classify_error_label(trace, "wrong_answer") == "citation_error"


def test_wrong_answer_with_invalid_citations_dropped_label_is_citation_error():
    trace = _trace(error_labels=["invalid_citations_dropped"])
    assert classify_error_label(trace, "wrong_answer") == "citation_error"


def test_wrong_answer_on_refused_trace_is_refusal_error():
    trace = _trace(refusal=True)
    assert classify_error_label(trace, "thumbs_down") == "refusal_error"


def test_wrong_answer_served_by_fallback_is_provider_error():
    trace = _trace(fallback_hop="tertiary")
    assert classify_error_label(trace, "wrong_answer") == "provider_error"


def test_wrong_answer_low_score_is_retrieval_failure():
    trace = _trace(error_labels=["low_score"])
    assert classify_error_label(trace, "wrong_answer") == "retrieval_failure"


def test_wrong_answer_no_context_is_retrieval_failure():
    trace = _trace(error_labels=["no_context"])
    assert classify_error_label(trace, "wrong_answer") == "retrieval_failure"


def test_wrong_answer_default_is_hallucination():
    trace = _trace()
    assert classify_error_label(trace, "wrong_answer") == "hallucination"


def test_invalid_citations_checked_before_fallback_hop():
    """Ưu tiên tín hiệu cụ thể nhất: nếu VỪA có invalid_citations VỪA bị
    fallback, vẫn phải là citation_error (nguyên nhân trực tiếp hơn)."""
    trace = _trace(invalid_citations=["chunk_x"], fallback_hop="secondary")
    assert classify_error_label(trace, "wrong_answer") == "citation_error"
