"""Unit test cho complexity routing + dynamic top-k (Phase 11, Module 8)."""

from __future__ import annotations

from src.optimization.routing import classify_complexity, dynamic_top_k, resolve_tier


def test_short_question_is_simple():
    assert classify_complexity("Học phí bao nhiêu?") == "simple"


def test_multi_part_question_is_hard():
    q = "Sinh viên vừa bị đình chỉ học vừa nợ học phí thì xử lý thế nào?"
    assert classify_complexity(q) == "hard"


def test_long_single_clause_question_is_medium():
    q = "Xin hỏi về quy trình xét tốt nghiệp đại học chính quy tại trường"
    assert len(q) > 60
    assert classify_complexity(q) == "medium"


def test_resolve_tier_maps_to_real_gateway_tiers():
    assert resolve_tier("Học phí bao nhiêu?") == "cheap"
    assert resolve_tier("Sinh viên vừa bị đình chỉ vừa nợ học phí thì sao?") == "strong"


def test_dynamic_top_k_borderline_score_increases_k():
    k = dynamic_top_k(scores=[1.15], min_score=1.10, base_k=5, max_k=10)
    assert k > 5


def test_dynamic_top_k_confident_score_decreases_k():
    k = dynamic_top_k(scores=[2.5], min_score=1.10, base_k=5, max_k=10)
    assert k < 5


def test_dynamic_top_k_mid_range_score_keeps_base():
    k = dynamic_top_k(scores=[1.7], min_score=1.10, base_k=5, max_k=10)
    assert k == 5


def test_dynamic_top_k_empty_scores_returns_base():
    assert dynamic_top_k(scores=[], min_score=1.10, base_k=5, max_k=10) == 5


def test_dynamic_top_k_never_exceeds_max_k():
    k = dynamic_top_k(scores=[1.15], min_score=1.10, base_k=9, max_k=10)
    assert k <= 10
