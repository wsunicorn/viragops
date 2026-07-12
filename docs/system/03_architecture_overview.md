# Architecture Overview

## Mục tiêu kiến trúc

Kiến trúc hướng tới một hệ thống RAG tiếng Việt production-like với đầy đủ năng lực LLMOps/RAGOps. Hệ thống không chỉ trả lời câu hỏi mà còn quản lý vòng đời dữ liệu, prompt, model, evaluation, deployment, monitoring và feedback.

## 9 module chính

| Module | Vai trò | Output chính |
|---|---|---|
| 1. DataOps/RAGOps | Ingest, clean, chunk, embed, index, version data | `data_version`, `index_version`, chunks |
| 2. Retrieval Experiment | So sánh chunking/retrieval/reranking | best retrieval config, metrics |
| 3. RAG Runtime | API hỏi đáp, context assembly, citation, refusal | answer, citations, trace_id |
| 4. PromptOps | Quản lý prompt lifecycle | prompt_version, prompt comparison |
| 5. Evaluation Engine | Đánh giá 4 tầng | eval report, metric scores |
| 6. Quality Gate | Chặn regression trước deploy | PASS/WARN/BLOCK |
| 7. Observability/Cost | Trace, metric, dashboard | latency, cost, error labels |
| 8. Optimization/Routing | Cache, compression, routing, fallback | optimized config |
| 9. Feedback Loop | Thu feedback, phân loại lỗi, cải tiến | improvement backlog |

## Luồng xử lý runtime

1. Người dùng gửi câu hỏi vào QA API.
2. API tạo `request_id` và `trace_id`.
3. Query được chuẩn hóa tiếng Việt.
4. Semantic cache kiểm tra câu hỏi tương tự.
5. Retrieval lấy candidate chunks từ Qdrant/OpenSearch.
6. Reranker sắp xếp lại context.
7. PromptOps cung cấp prompt version active.
8. Model Gateway chọn model/provider theo policy.
9. LLM sinh câu trả lời.
10. Guardrail kiểm tra citation/refusal/hallucination sơ bộ.
11. API trả answer, citations, confidence, trace_id.
12. Observability ghi trace, token, cost, latency.
13. Evaluation async hoặc batch đánh giá request.
14. Feedback nếu có được nối vào trace.

## Luồng xử lý thay đổi

Các thay đổi có thể đến từ:

- tài liệu nguồn mới;
- chunking strategy mới;
- embedding model mới;
- retrieval config mới;
- prompt version mới;
- model/provider config mới;
- code runtime mới.

Mọi thay đổi phải đi qua:

1. tạo version mới;
2. chạy smoke evaluation;
3. so sánh metric với baseline;
4. quality gate ra quyết định;
5. deploy nếu đạt;
6. theo dõi production-like metrics;
7. rollback nếu metric giảm dưới ngưỡng.

## Ranh giới module

- DataOps không gọi LLM generation.
- Retrieval Experiment không quyết định deploy.
- RAG Runtime không hard-code model.
- PromptOps không tự thay prompt active nếu chưa qua quality gate.
- Evaluation Engine không sửa dữ liệu, chỉ tính metric.
- Quality Gate không tự tạo metric, chỉ đọc kết quả eval và ra quyết định.
- Observability không thay đổi answer, chỉ ghi nhận và cảnh báo.
- Optimization không được giảm chất lượng vượt ngưỡng.
- Feedback Loop không sửa production trực tiếp, chỉ tạo candidate improvement.

## Storage chính

| Storage | Dữ liệu |
|---|---|
| PostgreSQL | metadata, prompt registry, config registry, feedback |
| Qdrant | dense/sparse vector index |
| ClickHouse | trace/event/metric nếu dùng Langfuse self-host |
| Redis/Valkey | semantic cache, queue nhẹ |
| MinIO/S3 | raw docs, processed docs, experiment artifacts |
| DVC/MLflow | data artifact, experiment metrics, reports |

## Kiến trúc deployment

Deployment local/full-scope gồm:

- `api`: FastAPI runtime;
- `frontend`: Next.js showcase/demo web app (đổi từ Streamlit/Gradio 2026-07-12 — xem `modules/10_frontend_showcase.md`), gọi thẳng `api` qua `/qa/query`, không truy cập trực tiếp storage nào khác;
- `qdrant`: vector database;
- `postgres`: metadata database;
- `valkey`: cache/queue;
- `litellm`: model gateway;
- `langfuse-web` và `langfuse-worker`: tracing/eval/prompt observability;
- `clickhouse`: event store;
- `minio`: blob store;
- `prometheus` và `grafana`: infra metrics/dashboard;
- `mlflow`: experiment tracking.

