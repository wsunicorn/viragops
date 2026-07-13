"""Unit test cho inter-judge agreement (Phase 8 remediation, 2026-07-13) —
thuần tính toán trên QuestionResult giả lập, không cần Qdrant/gateway thật
(test đó thuộc tests/integration/test_evaluation_runner.py).
"""

from __future__ import annotations

from src.evaluation.runner import QuestionResult, aggregate, inter_judge_agreement


def _result(judge: dict | None, judge2: dict | None) -> QuestionResult:
    return QuestionResult(
        question_id="q1",
        category="factoid",
        requires_refusal=False,
        requires_clarification=False,
        got_refusal=False,
        refusal_correct=True,
        retrieval_eval=None,
        context_precision=None,
        citation_accuracy=None,
        judge=judge,
        latency_ms=100,
        cost_usd=0.0,
        fallback_hop="primary",
        judge2=judge2,
    )


def test_inter_judge_agreement_none_when_no_judge2():
    results = [_result({"faithfulness": 1.0, "answer_relevance": 1.0, "context_relevance": 1.0, "hallucination": False}, None)]
    assert inter_judge_agreement(results) is None


def test_inter_judge_agreement_perfect_match():
    j = {"faithfulness": 1.0, "answer_relevance": 0.5, "context_relevance": 1.0, "hallucination": False}
    results = [_result(dict(j), dict(j))]
    agg = inter_judge_agreement(results)
    assert agg["n_pairs"] == 1
    assert agg["faithfulness_exact_match_rate"] == 1.0
    assert agg["faithfulness_mean_abs_diff"] == 0.0
    assert agg["hallucination_agreement_rate"] == 1.0


def test_inter_judge_agreement_disagreement():
    j1 = {"faithfulness": 1.0, "answer_relevance": 1.0, "context_relevance": 1.0, "hallucination": False}
    j2 = {"faithfulness": 0.0, "answer_relevance": 1.0, "context_relevance": 0.5, "hallucination": True}
    agg = inter_judge_agreement([_result(j1, j2)])
    assert agg["faithfulness_mean_abs_diff"] == 1.0
    assert agg["faithfulness_exact_match_rate"] == 0.0
    assert agg["context_relevance_mean_abs_diff"] == 0.5
    assert agg["hallucination_agreement_rate"] == 0.0


def test_inter_judge_agreement_skips_judge_errors():
    j_ok = {"faithfulness": 1.0, "answer_relevance": 1.0, "context_relevance": 1.0, "hallucination": False}
    results = [
        _result(j_ok, j_ok),
        _result({"error": "boom"}, j_ok),
        _result(j_ok, {"error": "boom"}),
    ]
    agg = inter_judge_agreement(results)
    assert agg["n_pairs"] == 1  # 2 câu lỗi bị loại khỏi phép so sánh


def test_aggregate_includes_inter_judge_agreement_key():
    j_ok = {"faithfulness": 1.0, "answer_relevance": 1.0, "context_relevance": 1.0, "hallucination": False}
    agg = aggregate([_result(j_ok, j_ok)])
    assert agg["inter_judge_agreement"]["n_pairs"] == 1

    agg_no_j2 = aggregate([_result(j_ok, None)])
    assert agg_no_j2["inter_judge_agreement"] is None
