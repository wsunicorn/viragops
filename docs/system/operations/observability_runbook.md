# Observability Runbook

## Mục tiêu

Hướng dẫn đọc trace, metric và dashboard để debug lỗi RAG.

## Khi một câu trả lời sai

Kiểm tra theo thứ tự:

1. Mở trace bằng `trace_id`.
2. Xem normalized query.
3. Xem retrieved chunks.
4. Kiểm relevant chunks có nằm trong top-k không.
5. Xem rerank score.
6. Xem prompt version.
7. Xem model/provider.
8. Xem answer và citations.
9. Xem evaluation labels.
10. Gắn error label nếu chưa có.

## Mapping lỗi sang nguyên nhân

| Triệu chứng | Kiểm tra | Khả năng |
|---|---|---|
| Answer sai, context sai | retrieved chunks | retrieval_failure |
| Answer sai, context đúng | prompt/model output | hallucination |
| Answer đúng, citation sai | citation parser/metadata | citation_error |
| Từ chối dù có tài liệu | context threshold/refusal prompt | refusal_error |
| Request chậm | span latency | reranker/model/provider |
| Cost tăng | token usage/model route | prompt/context/model routing |
| Query giống nhau nhưng answer cũ | cache key | stale cache/data_version |

## Dashboard cần xem hàng ngày

- Request volume.
- p95 latency.
- Cost/request.
- Error rate.
- Retrieval hit rate.
- Faithfulness trend.
- Hallucination alerts.
- Provider fallback rate.
- Cache hit rate.
- Data freshness.

## Alert và hành động

> **Implement thật (Phase 10, 2026-07-14):** 4/6 alert dưới đây có rule
> Prometheus thật (`config/prometheus_alert_rules.yml`, verify
> `health=ok`) — `p95 latency high`/`cost spike`/`provider fallback
> high` + `error rate high` (thêm mới, không có trong bảng gốc). 2 alert
> còn lại (`hallucination high`, `retrieval hit low`) KHÔNG có rule
> Prometheus vì cần LLM-judge/ground-truth relevance — không tính được
> real-time trên mỗi request thật (quá tốn quota để judge mỗi câu). Cơ
> chế tương đương THẬT: Quality Gate (Phase 9, `src/qualitygate/`) tự
> BLOCK/WARN đúng 2 chỉ số này mỗi lần chạy Evaluation Engine, xem
> CHECKLIST Phase 9. Chưa có Alertmanager/kênh Slack/email thật — rule
> hiện "firing" trong Prometheus/Grafana UI, chưa tự động gửi ra ngoài.

| Alert | Ngưỡng | Hành động |
|---|---|---|
| p95 latency high | > 6s | Kiểm reranker/model/provider |
| cost spike | > budget | Kiểm route model, token, cache |
| hallucination high | > 5% | Chạy targeted eval, sửa prompt/retrieval — xem Quality Gate (Phase 9) |
| retrieval hit low | < 85% | Kiểm index/chunking/embedding — xem Quality Gate (Phase 9) |
| data stale | index age > policy | Reindex — `viragops_data_age_days` (Grafana panel "Data freshness") |
| provider fallback high | > 20% | Kiểm provider health/API key/rate limit |

## Báo cáo tuần

Mỗi tuần ghi:

- số request;
- cost tổng;
- p95 latency;
- top 5 failed queries;
- top error clusters;
- thay đổi prompt/data/model;
- metric trước/sau thay đổi;
- action items.

