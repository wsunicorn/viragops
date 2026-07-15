# Experiment 4 — Quality Gate Effectiveness

16 kịch bản giả lập THẬT (tái dùng nguyên fixture `tests/unit/test_quality_gate.py::SIMULATED_CHANGES`, không tạo bản sao thứ 3 — file test đã tự cảnh báo rủi ro trùng lặp với `config/quality_gate.yaml`). Cơ cấu THẬT của fixture là **9 xấu / 4 cảnh báo / 3 tốt** — khác với cơ cấu "8 tốt/8 xấu" ghi trong `experiment_plan.md` (chênh lệch có chủ đích ghi rõ, không tự ý sửa fixture đã verify từ Phase 9 chỉ để khớp con số kế hoạch).

## Confusion matrix (nhị phân — positive = "nên BLOCK", 9 kịch bản xấu)

| | Actual BLOCK | Actual not-BLOCK |
|---|---:|---:|
| Expected BLOCK (positive) | TP=9 | FN=0 |
| Expected not-BLOCK (negative) | FP=0 | TN=7 |

Precision=1.000, Recall=1.000

## Confusion matrix đầy đủ (3x3, expected x actual)

| Expected \ Actual | PASS | WARN | BLOCK |
|---|---:|---:|---:|
| PASS | 3 | 0 | 0 |
| WARN | 0 | 4 | 0 |
| BLOCK | 0 | 0 | 9 |

## Gate latency (đo thật, 16 lần gọi `evaluate_gate()`)

p50=0.006ms, p95=0.011ms — hàm thuần offline (không I/O), độ trễ không đáng kể, không phải điểm nghẽn của CI pipeline.

## Chi tiết 16 kịch bản

| Label | Expected | Actual | Match | Vi phạm |
|---|---|---|---|---|
| prompt_regression_faithfulness_collapse | BLOCK | BLOCK | ✅ | faithfulness(threshold) |
| retrieval_config_regression_recall_collapse | BLOCK | BLOCK | ✅ | recall_at_5(threshold) |
| guardrail_policy_hallucination_spike | BLOCK | BLOCK | ✅ | hallucination_rate(threshold) |
| prompt_refusal_policy_broken | BLOCK | BLOCK | ✅ | refusal_accuracy(threshold) |
| model_gateway_latency_regression | BLOCK | BLOCK | ✅ | p95_latency_seconds(threshold) |
| code_runtime_error_spike | BLOCK | BLOCK | ✅ | error_rate(threshold) |
| prompt_answer_relevance_drop | BLOCK | BLOCK | ✅ | answer_relevance(threshold) |
| chunking_change_multi_metric_regression | BLOCK | BLOCK | ✅ | recall_at_5(threshold), refusal_accuracy(threshold) |
| gradual_prompt_drift_within_floor | BLOCK | BLOCK | ✅ | faithfulness(regression) |
| citation_prompt_regression_warning_only | WARN | WARN | ✅ | citation_accuracy(threshold) |
| model_gateway_cost_increase | WARN | WARN | ✅ | cost_per_request_usd(threshold) |
| chunking_change_minor_citation_dip | WARN | WARN | ✅ | citation_accuracy(threshold) |
| retrieval_config_cost_and_citation_both_warn | WARN | WARN | ✅ | citation_accuracy(threshold), cost_per_request_usd(threshold) |
| cost_aware_prompt_no_quality_loss | PASS | PASS | ✅ | — |
| neutral_retrieval_config_noop | PASS | PASS | ✅ | — |
| small_latency_improvement | PASS | PASS | ✅ | — |

## Kết luận

- Recall thật = 1.000 (chặn 9/9 thay đổi xấu) — đạt tiêu chí gốc "chặn >= 8/9" (module doc), khớp đúng assertion thật trong `test_16_simulated_changes_suite` (`true_positives >= 8`, `false_negatives == 0`).
- Precision thật = 1.000 — 0 false positive trên 9 lần BLOCK.
- 4 kịch bản WARN đều đúng (không lẫn vào PASS/BLOCK) — gate phân biệt đúng 3 mức nghiêm trọng, không chỉ nhị phân.