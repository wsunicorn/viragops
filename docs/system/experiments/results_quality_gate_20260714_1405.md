# Quality Gate report — 20260714_1405 UTC

> gate_config_id=`gate_default_v1`, eval_run mode=`smoke` (`20260714_1403`), baseline=`smoke` (`20260714_0320`)

## Quyết định: **BLOCK**

Có ít nhất 1 critical metric vi phạm hoặc regression vượt ngưỡng — giữ version cũ.

## Critical metrics

| Metric | Giá trị | Baseline | Vi phạm |
|---|---:|---:|---|
| recall_at_5 | 0.9000 | 0.9054 | ✅ |
| faithfulness | 0.9474 | 0.9500 | ✅ |
| answer_relevance | 0.9737 | 0.9625 | ✅ |
| hallucination_rate | 0.0789 | n/a | ❌ |
| refusal_accuracy | 0.8958 | n/a | ❌ |
| p95_latency_seconds | 2.1010 | 1.2870 | ❌ |
| error_rate | 0.0000 | 0.0000 | ✅ |

## Warning metrics

| Metric | Giá trị | Baseline | Vi phạm |
|---|---:|---:|---|
| citation_accuracy | 0.7745 | 0.8380 | ❌ |
| cost_per_request_usd | 0.0010 | 0.0009 | ✅ |

## Chi tiết vi phạm

- **[CRITICAL/threshold]** hallucination_rate=0.0789 > max 0.05
- **[CRITICAL/threshold]** refusal_accuracy=0.8958 < min 0.9
- **[CRITICAL/regression]** p95_latency_seconds tăng 0.8140 so baseline (1.2870 -> 2.1010), vượt max_quality_drop=0.03
- **[WARNING/threshold]** citation_accuracy=0.7745 < min 0.85