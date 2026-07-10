# viRAGops — Hỏi đáp tài liệu tiếng Việt (IUH)

> **vi**etnamese **RAG** **ops** — *every change goes through the gate.*

Nền tảng LLMOps/RAGOps full-scope cho hệ thống hỏi đáp **Quy chế đào tạo + FAQ sinh viên Trường ĐH Công nghiệp TP.HCM (IUH)** dựa trên Retrieval-Augmented Generation — khóa luận tốt nghiệp.

> Bản đồ tổng thể đề tài: [docs/sumarize.md](docs/sumarize.md) · Blueprint chi tiết: [docs/llmops_thesis_blueprint.md](docs/llmops_thesis_blueprint.md) · Checklist 12 phase: [docs/system/CHECKLIST_IMPLEMENTATION.md](docs/system/CHECKLIST_IMPLEMENTATION.md)

## Trạng thái

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 1 | Skeleton, config, healthcheck, CI | ✅ hoàn tất |
| 2 | Dữ liệu IUH + golden set 300 câu | ⬜ |
| 3-12 | Xem checklist | ⬜ |

## Chạy local (không Docker)

```bash
# 1. Tạo môi trường (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"

# 2. Cấu hình
copy .env.example .env           # rồi điền POSTGRES_PASSWORD, API keys...

# 3. Chạy API
uvicorn src.api.main:app --reload --port 8000
```

Kiểm tra:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/dependencies
# Swagger UI: http://localhost:8000/docs
```

## Chạy bằng Docker Compose

```bash
copy .env.example .env           # điền POSTGRES_PASSWORD (bắt buộc)
docker compose up -d --build
curl http://localhost:8000/health/dependencies
```

Phase 1 gồm 4 service lõi: `api`, `qdrant`, `postgres`, `valkey`. Các service còn lại (LiteLLM, Langfuse, ClickHouse, MinIO, Prometheus/Grafana, MLflow) được thêm ở đúng phase — xem [deployment doc](docs/system/operations/deployment_docker_compose.md).

## Test & lint

```bash
pytest tests/unit -q
ruff check src tests
```

## Cấu trúc project

```
config/          # Config có version: retrieval, prompts, model_gateway, quality_gate
data/            # raw / processed / chunks / test_sets (theo dõi bằng DVC)
src/
├── api/         # FastAPI runtime (Phase 1: health; Phase 5: /qa/query ...)
├── common/      # settings, config_loader
├── dataops/     # Module 1 — ingest/clean/chunk/embed/index (Phase 3)
├── retrieval/   # Module 2 — retrieval experiments (Phase 4)
├── rag/         # Module 3 — RAG orchestrator (Phase 5)
├── promptops/   # Module 4 — prompt registry (Phase 6)
├── evaluation/  # Module 5 — eval 4 tầng (Phase 8)
├── quality_gate/# Module 6 — PASS/WARN/BLOCK (Phase 9)
├── observability/ # Module 7 (Phase 10)
├── optimization/  # Module 8 (Phase 11)
└── feedback/    # Module 9 (Phase 11)
scripts/         # CLI: ingest, run_evaluation, check_gate, run_experiment...
tests/           # unit / integration / e2e
docs/            # Toàn bộ tài liệu thiết kế + thesis blueprint
```

## Nguyên tắc bất biến

- Mọi artifact quan trọng có version (`config/README.md`).
- Không hard-code provider/model — mọi model call đi qua gateway config.
- Mọi thay đổi rủi ro phải qua evaluation + quality gate trước khi active.
- Không trả lời khi thiếu căn cứ trong tài liệu (refusal + citation bắt buộc).
- Không commit secret; `.env` nằm ngoài git.
