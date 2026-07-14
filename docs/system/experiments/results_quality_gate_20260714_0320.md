# Quality Gate report — 20260714_0320 UTC

> gate_config_id=`gate_default_v1`, eval_run mode=`smoke` (`20260714_0320`), KHÔNG có baseline (chỉ so ngưỡng tuyệt đối, không check regression)

## Quyết định: **BLOCK**

Có ít nhất 1 critical metric vi phạm hoặc regression vượt ngưỡng — giữ version cũ.

## Critical metrics

| Metric | Giá trị | Baseline | Vi phạm |
|---|---:|---:|---|
| recall_at_5 | 0.9054 | n/a | ✅ |
| faithfulness | 0.9500 | n/a | ✅ |
| answer_relevance | 0.9625 | n/a | ✅ |
| hallucination_rate | 0.1000 | n/a | ❌ |
| refusal_accuracy | 0.9000 | n/a | ✅ |
| p95_latency_seconds | 1.2870 | n/a | ✅ |
| error_rate | 0.0000 | n/a | ✅ |

## Warning metrics

| Metric | Giá trị | Baseline | Vi phạm |
|---|---:|---:|---|
| citation_accuracy | 0.8380 | n/a | ❌ |
| cost_per_request_usd | 0.0009 | n/a | ✅ |

## Chi tiết vi phạm

- **[CRITICAL/threshold]** hallucination_rate=0.1000 > max 0.05
- **[WARNING/threshold]** citation_accuracy=0.8380 < min 0.85