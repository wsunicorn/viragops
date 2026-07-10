# Deployment bằng Docker Compose

## Mục tiêu

Triển khai hệ thống full-scope ở môi trường local/production-like bằng Docker Compose. Đây là baseline bắt buộc trước khi nghĩ đến K3s/Kubernetes.

## Service chính

| Service | Vai trò |
|---|---|
| `api` | FastAPI RAG runtime |
| `frontend` | Streamlit/Gradio demo |
| `qdrant` | Vector database |
| `postgres` | Metadata, prompt, feedback, config |
| `valkey` | Cache/queue |
| `litellm` | Model gateway |
| `langfuse-web` | Langfuse UI/API |
| `langfuse-worker` | Langfuse background worker |
| `clickhouse` | Langfuse event store |
| `minio` | Blob/object storage |
| `prometheus` | Metrics scraping |
| `grafana` | Dashboard |
| `mlflow` | Experiment tracking |

## Thứ tự triển khai

1. Chạy hạ tầng nhẹ: Postgres, Valkey, Qdrant.
2. Chạy API healthcheck.
3. Chạy LiteLLM với một provider.
4. Chạy frontend demo.
5. Thêm Prometheus/Grafana.
6. Thêm MLflow.
7. Thêm Langfuse stack.
8. Thêm MinIO/ClickHouse nếu Langfuse self-host yêu cầu.
9. Chạy ingest thử.
10. Chạy QA thử.
11. Chạy smoke eval.

## Biến môi trường bắt buộc

- `POSTGRES_PASSWORD`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY` nếu dùng Claude
- `GEMINI_API_KEY` nếu dùng Gemini
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

## Healthcheck

| Service | Check |
|---|---|
| API | `GET /health` |
| Qdrant | HTTP port 6333 |
| Postgres | connection test |
| Valkey | ping |
| LiteLLM | model list hoặc test completion |
| Langfuse | web UI reachable |
| Grafana | web UI reachable |
| MLflow | tracking UI reachable |

## Acceptance criteria

- `docker compose up` chạy được không lỗi critical.
- API healthcheck pass.
- Qdrant ghi/đọc được vector test.
- LiteLLM gọi được model test.
- Một request QA có trace_id.
- Grafana có dashboard request/latency.
- Langfuse có trace nếu bật.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Langfuse stack nặng | Chạy API/Qdrant/LiteLLM trước, thêm Langfuse sau |
| Port conflict | Đổi port trong `.env` hoặc compose override |
| API key thiếu | Healthcheck provider phải báo lỗi rõ |
| ClickHouse/MinIO lỗi | Dùng docs Langfuse chính thức để sync version |

