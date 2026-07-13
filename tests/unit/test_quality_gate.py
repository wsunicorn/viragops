"""Unit tests for the Quality Gate decision logic (Phase 9, Module 6).

Includes the "16 simulated changes" regression suite the module doc
(modules/06_quality_gate_cicd.md acceptance criteria) asks for: run the
gate against realistic aggregate JSONs representing 16 different
prompt/model/retrieval/code changes and confirm it blocks at least 8 bad
ones, warns on borderline ones, and passes good/neutral ones — all
offline (no Qdrant/Postgres/LiteLLM/Gemini calls needed, matching
gate.py's design: it judges numbers a report already produced).
"""

from __future__ import annotations

import copy

import yaml

from src.qualitygate.gate import evaluate_gate

CONFIG = yaml.safe_load("""
gate_config_id: gate_test_v1
critical_metrics:
  recall_at_5:
    min: 0.85
  faithfulness:
    min: 0.85
  answer_relevance:
    min: 0.80
  hallucination_rate:
    max: 0.05
  refusal_accuracy:
    min: 0.90
  p95_latency_seconds:
    max: 6.0
  error_rate:
    max: 0.01
warning_metrics:
  citation_accuracy:
    min: 0.85
  cost_per_request_usd:
    max: 0.005
regression:
  max_quality_drop: 0.03
""")

# Baseline representative of a healthy production run (values in the
# neighborhood of what Phase 8's real primary-hop numbers showed).
BASELINE = {
    "retrieval": {"recall_at_k": 0.93},
    "faithfulness": 0.95,
    "answer_relevance": 0.93,
    "hallucination_rate": 0.03,
    "refusal_accuracy": 0.96,
    "p95_latency_ms": 1500,
    "error_rate": 0.0,
    "citation_accuracy": 0.88,
    "avg_cost_usd": 0.0004,
}


def _variant(**overrides) -> dict:
    agg = copy.deepcopy(BASELINE)
    for key, value in overrides.items():
        if key == "recall_at_k":
            agg["retrieval"]["recall_at_k"] = value
        else:
            agg[key] = value
    return agg


# --- Core decision logic -----------------------------------------------


def test_pass_when_identical_to_baseline():
    decision = evaluate_gate(BASELINE, CONFIG, BASELINE)
    assert decision.status == "PASS"
    assert decision.critical_violations == []
    assert decision.warning_violations == []


def test_pass_without_baseline_when_thresholds_met():
    decision = evaluate_gate(BASELINE, CONFIG, baseline=None)
    assert decision.status == "PASS"
    assert decision.baseline_metrics is None


def test_block_on_absolute_threshold_violation():
    current = _variant(faithfulness=0.60)
    decision = evaluate_gate(current, CONFIG, baseline=None)
    assert decision.status == "BLOCK"
    assert any(v.metric == "faithfulness" and v.reason == "threshold" for v in decision.critical_violations)


def test_warn_on_warning_metric_violation_only():
    current = _variant(citation_accuracy=0.70)
    decision = evaluate_gate(current, CONFIG, baseline=None)
    assert decision.status == "WARN"
    assert decision.critical_violations == []
    assert any(v.metric == "citation_accuracy" for v in decision.warning_violations)


def test_missing_critical_metric_is_fail_closed_block():
    current = _variant()
    del current["faithfulness"]
    decision = evaluate_gate(current, CONFIG, baseline=None)
    assert decision.status == "BLOCK"
    assert any(v.reason == "missing" for v in decision.critical_violations)


def test_regression_blocks_even_above_absolute_floor():
    # 0.95 -> 0.90 vẫn > min 0.85 (không fail threshold) nhưng giảm 0.05 >
    # max_quality_drop 0.03 so baseline -> vẫn phải BLOCK (đúng tinh thần
    # "regression margin" trong module doc, không chỉ đo ngưỡng tuyệt đối).
    current = _variant(faithfulness=0.90)
    decision = evaluate_gate(current, CONFIG, BASELINE)
    assert decision.status == "BLOCK"
    assert any(v.metric == "faithfulness" and v.reason == "regression" for v in decision.critical_violations)


def test_regression_check_skipped_without_baseline():
    current = _variant(faithfulness=0.90)  # would regress-block WITH a baseline
    decision = evaluate_gate(current, CONFIG, baseline=None)
    assert decision.status == "PASS"


def test_small_improvement_passes():
    current = _variant(recall_at_k=0.95, faithfulness=0.97)
    decision = evaluate_gate(current, CONFIG, BASELINE)
    assert decision.status == "PASS"


# --- 16 simulated changes (module doc acceptance criteria) --------------
# (label, aggregate overrides, expected status)
SIMULATED_CHANGES = [
    # --- 9 bad changes: should BLOCK ---
    ("prompt_regression_faithfulness_collapse", {"faithfulness": 0.70}, "BLOCK"),
    ("retrieval_config_regression_recall_collapse", {"recall_at_k": 0.55}, "BLOCK"),
    ("guardrail_policy_hallucination_spike", {"hallucination_rate": 0.18}, "BLOCK"),
    ("prompt_refusal_policy_broken", {"refusal_accuracy": 0.50}, "BLOCK"),
    ("model_gateway_latency_regression", {"p95_latency_ms": 9000}, "BLOCK"),
    ("code_runtime_error_spike", {"error_rate": 0.06}, "BLOCK"),
    ("prompt_answer_relevance_drop", {"answer_relevance": 0.55}, "BLOCK"),
    ("chunking_change_multi_metric_regression", {"recall_at_k": 0.70, "refusal_accuracy": 0.80}, "BLOCK"),
    ("gradual_prompt_drift_within_floor", {"faithfulness": 0.905}, "BLOCK"),  # 0.045 drop > 0.03 margin
    # --- 4 borderline changes: should WARN (critical OK, warning fails) ---
    ("citation_prompt_regression_warning_only", {"citation_accuracy": 0.72}, "WARN"),
    ("model_gateway_cost_increase", {"avg_cost_usd": 0.008}, "WARN"),
    ("chunking_change_minor_citation_dip", {"citation_accuracy": 0.80}, "WARN"),
    ("retrieval_config_cost_and_citation_both_warn", {"citation_accuracy": 0.75, "avg_cost_usd": 0.01}, "WARN"),
    # --- 3 good/neutral changes: should PASS ---
    ("cost_aware_prompt_no_quality_loss", {"avg_cost_usd": 0.0002}, "PASS"),
    ("neutral_retrieval_config_noop", {}, "PASS"),
    ("small_latency_improvement", {"p95_latency_ms": 1200}, "PASS"),
]


def test_16_simulated_changes_suite():
    assert len(SIMULATED_CHANGES) == 16

    results = []
    for label, overrides, expected in SIMULATED_CHANGES:
        current = _variant(**overrides)
        decision = evaluate_gate(current, CONFIG, BASELINE)
        results.append((label, expected, decision.status))

    mismatches = [(label, exp, got) for label, exp, got in results if exp != got]
    assert mismatches == [], f"gate decision mismatch: {mismatches}"

    bad_labels = {label for label, expected, _ in results if expected == "BLOCK"}
    true_positives = sum(1 for label, expected, got in results if expected == "BLOCK" and got == "BLOCK")
    false_negatives = sum(1 for label, expected, got in results if expected == "BLOCK" and got != "BLOCK")

    assert len(bad_labels) == 9
    assert true_positives >= 8  # acceptance criteria: chặn >= 8 thay đổi xấu giả lập
    assert false_negatives == 0

    good_or_neutral = [got for label, expected, got in results if expected in ("PASS", "WARN")]
    assert all(status != "BLOCK" for status in good_or_neutral)
