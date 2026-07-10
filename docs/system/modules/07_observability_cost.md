# Module 7 - Observability và Cost Monitoring

## Mục tiêu

Theo dõi request, trace, latency, token, cost, retrieval hit rate, hallucination/error labels và data freshness. Module này giúp debug hệ thống RAG khi câu trả lời sai hoặc chi phí tăng.

## Trách nhiệm

- Ghi trace cho mỗi request.
- Ghi span retrieval, rerank, prompt, model, evaluation.
- Tính token và cost/request.
- Theo dõi latency p50/p95/p99.
- Theo dõi error rate và provider fallback.
- Hiển thị dashboard vận hành.
- Cảnh báo cost spike, hallucination, stale data.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | runtime events, eval results, gateway events |
| Output | traces, metrics, dashboard panels, alerts |
| Storage | Langfuse, ClickHouse, Prometheus, Grafana |

## Trace fields bắt buộc

- `trace_id`;
- `request_id`;
- `session_id`;
- `user_query`;
- `normalized_query`;
- `retrieved_chunks`;
- `prompt_version`;
- `model_provider`;
- `model_name`;
- `input_tokens`;
- `output_tokens`;
- `cost_usd`;
- `latency_ms`;
- `data_version`;
- `index_version`;
- `error_labels`;
- `feedback_id`.

## Dashboard panels

1. Request volume.
2. Latency p50/p95/p99.
3. Token usage.
4. Cost/request.
5. Faithfulness trend.
6. Retrieval hit rate.
7. Hallucination alerts.
8. Top failed queries.
9. Prompt version comparison.
10. Model/provider usage.
11. Cache hit rate.
12. Data freshness.
13. Provider fallback rate.
14. Trace timeline.

## Task triển khai

- Integrate Langfuse tracing.
- Add OpenTelemetry spans.
- Add Prometheus metrics endpoint.
- Build Grafana dashboard.
- Track token/cost via Model Gateway.
- Add error labels from Evaluation Engine.
- Add alert rules.

## Acceptance criteria

- Mỗi QA request có trace_id.
- Trace xem được retrieval, prompt, model, answer.
- Dashboard có ít nhất 12 panel.
- Cost/request hiển thị đúng.
- p95 latency hiển thị đúng.
- Có alert cho hallucination/cost spike/stale data.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Trace thiếu span | Middleware chưa bao quanh đủ bước | Bắt buộc span per stage |
| Cost sai | Provider pricing không cập nhật | Giá nằm trong config và versioned |
| Dashboard nhiều nhưng vô dụng | Không có action từ metric | Gắn runbook cho từng alert |
| Log lộ dữ liệu | Log raw PII/secret | Masking và log policy |

## Checklist hoàn tất

- [ ] Langfuse tracing hoạt động.
- [ ] OpenTelemetry spans có tên nhất quán.
- [ ] Prometheus endpoint hoạt động.
- [ ] Grafana dashboard có 12+ panel.
- [ ] Cost tracking hoạt động.
- [ ] Error labels xuất hiện trong trace.
- [ ] Alert rules có runbook tương ứng.

