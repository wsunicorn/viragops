# Deployment bằng Docker Compose

## Mục tiêu

Triển khai hệ thống full-scope ở môi trường local/production-like bằng Docker Compose. Đây là baseline bắt buộc trước khi nghĩ đến K3s/Kubernetes.

## Service chính

| Service | Vai trò |
|---|---|
| `api` | FastAPI RAG runtime |
| `frontend` | Next.js showcase/QA-demo/dashboard web app (đổi từ Streamlit/Gradio 2026-07-12) |
| `qdrant` | Vector database |
| `postgres` | Metadata, prompt, feedback, config |
| `valkey` | Cache/queue |
| `litellm` | Model gateway |
| `prometheus` | Metrics scraping (`GET /metrics`, Phase 10) |
| `grafana` | Dashboard (Phase 10, 16 panel, xem `config/grafana/dashboards/viragops_overview.json`) |
| `mlflow` | Experiment tracking |

**Langfuse (Phase 10) KHÔNG chạy trong compose** — dùng **Cloud** (free
tier, xem CHECKLIST Phase 10 quyết định): máy dev hạn chế tài nguyên +
dự án đã hay gặp trục trặc stack Docker nặng (Phase 1/3), tự host thêm
`langfuse-web`/`langfuse-worker`+`clickhouse`+`minio` (4 container nữa)
không đáng đánh đổi khi Cloud free tier đủ dùng cho quy mô đồ án. Chỉ cần
`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` trong `.env` (tự tạo tài
khoản tại cloud.langfuse.com).

## Thứ tự triển khai

1. Chạy hạ tầng nhẹ: Postgres, Valkey, Qdrant.
2. Chạy API healthcheck.
3. Chạy LiteLLM với một provider.
4. Chạy frontend (Next.js, `npm run build && npm start` hoặc container riêng — xem `modules/10_frontend_showcase.md`).
5. Thêm Prometheus/Grafana (`docker compose up -d prometheus grafana`).
6. Thêm MLflow.
7. Cấu hình Langfuse Cloud (`.env`: `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`) — không cần compose service.
8. Chạy ingest thử.
9. Chạy QA thử.
10. Chạy smoke eval.

## Biến môi trường bắt buộc

- `POSTGRES_PASSWORD`
- `GEMINI_API_KEY` (provider thật đang dùng, xem CHECKLIST Phase 7 — OpenAI/Anthropic chưa có key)
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `GRAFANA_ADMIN_PASSWORD` (tuỳ chọn, mặc định `admin`)

## Healthcheck

| Service | Check |
|---|---|
| API | `GET /health` |
| Qdrant | HTTP port 6333 |
| Postgres | connection test |
| Valkey | ping |
| LiteLLM | model list hoặc test completion |
| Prometheus | `GET /-/healthy`, target `viragops-api` status `up` |
| Grafana | `GET /api/health` |
| Langfuse | `auth_check()` qua SDK (Cloud, không có endpoint local) |
| MLflow | tracking UI reachable |

## Acceptance criteria

- `docker compose up` chạy được không lỗi critical.
- API healthcheck pass.
- Qdrant ghi/đọc được vector test.
- LiteLLM gọi được model test.
- Một request QA có trace_id, xuất hiện thật trên Langfuse Cloud (verify
  2026-07-14 qua REST API `GET /api/public/traces/{id}`).
- Grafana có dashboard request/latency — verify thật 2026-07-14: 16 panel
  load đúng, query qua Grafana datasource proxy trả dữ liệu thật khớp
  Prometheus.
- Prometheus target `viragops-api` health = `up`, 4 alert rule load
  `health=ok`.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Port conflict | Đổi port trong `.env` hoặc compose override (Grafana đã đổi sang 3001 vì 3000 dùng cho frontend) |
| API key thiếu | Healthcheck provider phải báo lỗi rõ |
| Langfuse Cloud rate limit (free tier) | Theo dõi qua Langfuse dashboard; chưa chạm giới hạn ở quy mô đồ án |

