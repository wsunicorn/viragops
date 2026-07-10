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

| Alert | Ngưỡng | Hành động |
|---|---|---|
| p95 latency high | > 6s | Kiểm reranker/model/provider |
| cost spike | > budget | Kiểm route model, token, cache |
| hallucination high | > 5% | Chạy targeted eval, sửa prompt/retrieval |
| retrieval hit low | < 85% | Kiểm index/chunking/embedding |
| data stale | index age > policy | Reindex |
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

