# viRAGops — Hỏi đáp tài liệu tiếng Việt (IUH)

> **vi**etnamese **RAG** **ops** — *every change goes through the gate.*

Nền tảng LLMOps/RAGOps full-scope cho hệ thống hỏi đáp **Quy chế đào tạo + FAQ sinh viên Trường ĐH Công nghiệp TP.HCM (IUH)** dựa trên Retrieval-Augmented Generation — khóa luận tốt nghiệp.

> Bản đồ tổng thể đề tài: [docs/sumarize.md](docs/sumarize.md) · Blueprint chi tiết: [docs/llmops_thesis_blueprint.md](docs/llmops_thesis_blueprint.md) · Checklist 12 phase: [docs/system/CHECKLIST_IMPLEMENTATION.md](docs/system/CHECKLIST_IMPLEMENTATION.md) · Kết quả thực nghiệm: [docs/system/experiments/](docs/system/experiments/)

## Trạng thái

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 1 | Skeleton, config, healthcheck, CI | ✅ hoàn tất |
| 2 | Dữ liệu IUH + golden set 300 câu | ✅ hoàn tất |
| 3 | DataOps: chunk/embed/index (Module 1) | ✅ hoàn tất |
| 4 | Retrieval experiment (Module 2) | ✅ hoàn tất |
| 5 | RAG runtime (Module 3) | ✅ hoàn tất |
| 6 | PromptOps registry (Module 4) | ✅ hoàn tất |
| 7 | Model Gateway — LiteLLM + fallback (Module 3) | ✅ hoàn tất |
| 8 | Evaluation Engine (Module 5) | ✅ hoàn tất |
| 9 | CI/CD Quality Gate (Module 6) | ✅ hoàn tất |
| 10 | Observability — Langfuse + Prometheus/Grafana (Module 7) | ✅ hoàn tất |
| 11 | Feedback Loop + Optimization/Routing (Module 8/9) | ✅ hoàn tất |
| 12 | Thực nghiệm tổng hợp + báo cáo + demo | 🔶 đang làm (6 experiment report đã xong; chương báo cáo khóa luận + slide chưa viết) |

Frontend showcase (Next.js) được xây sớm hơn kế hoạch, bắt đầu giữa Phase 8 — xem `frontend/README.md`.

## Chạy demo đầy đủ (backend + frontend)

```bash
# 1. Cấu hình
copy .env.example .env
# điền: POSTGRES_PASSWORD, GEMINI_API_KEY (bắt buộc để trả lời thật),
# LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY (tuỳ chọn, xem Phase 10)

# 2. Hạ tầng lõi + backend
docker compose up -d qdrant postgres valkey litellm prometheus grafana
python scripts/init_postgres_schema.py
python scripts/seed_prompts.py
uvicorn src.api.main:app --port 8000
# (nếu chưa ingest dữ liệu lần nào: python scripts/ingest_data.py --recreate-collection)

# 3. Frontend (terminal khác)
cd frontend
npm install
npm run dev
```

Mở `http://localhost:3000` (showcase + `/demo` hỏi-đáp thật + `/dashboard` số liệu thực nghiệm), API tại `http://localhost:8000/docs`, Grafana tại `http://localhost:3001`. Chi tiết frontend: [frontend/README.md](frontend/README.md). Chi tiết deploy đầy đủ (thứ tự service, biến môi trường, healthcheck): [docs/system/operations/deployment_docker_compose.md](docs/system/operations/deployment_docker_compose.md).

## Chạy local (chỉ backend, không Docker cho API)

```bash
# 1. Tạo môi trường (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev,dataops,ragops,observability,reporting]"

# 2. Cấu hình
copy .env.example .env

# 3. Hạ tầng (Qdrant/Postgres/Valkey/LiteLLM) qua Docker, API chạy local
docker compose up -d qdrant postgres valkey litellm
uvicorn src.api.main:app --reload --port 8000
```

Kiểm tra:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/dependencies
# Swagger UI: http://localhost:8000/docs
```

## Test & lint

```bash
pytest -q                  # unit + integration (tự skip phần cần Postgres/Qdrant nếu service tắt)
ruff check .
```

## Cấu trúc project

```
config/          # Config có version: retrieval, prompts, model_gateway, quality_gate, optimization
data/            # raw / processed / chunks / test_sets / eval / traces
frontend/        # Next.js showcase + demo + dashboard (npm install && npm run dev)
src/
├── api/           # FastAPI runtime — qa, feedback, prompts, metrics, health
├── common/        # settings, config_loader
├── dataops/       # Module 1 — ingest/clean/chunk/embed/index (Phase 3)
├── retrieval/     # Module 2 — retrieval experiments (Phase 4)
├── rag/           # Module 3 — RAG orchestrator + Model Gateway client (Phase 5/7)
├── promptops/     # Module 4 — prompt registry (Phase 6)
├── evaluation/    # Module 5 — eval 4 tầng (Phase 8)
├── qualitygate/   # Module 6 — PASS/WARN/BLOCK (Phase 9)
├── observability/ # Module 7 — Langfuse tracing + Prometheus metrics (Phase 10)
├── feedback/      # Module 9 — feedback API + error classifier + clustering (Phase 11)
└── optimization/  # Module 8 — semantic cache/compression/routing (Phase 11)
scripts/         # CLI: ingest, run_evaluation, check_gate, run_experiment*, seed_*
tests/           # unit / integration
docs/
├── system/        # charter, requirements, architecture, module doc, experiments, operations
├── figures/       # hình minh hoạ báo cáo
└── llmops_thesis_blueprint.md  # dàn ý + kế hoạch khóa luận đầy đủ
```

## Nguyên tắc bất biến

- Mọi artifact quan trọng có version (`config/README.md`).
- Không hard-code provider/model — mọi model call đi qua gateway config.
- Mọi thay đổi rủi ro phải qua evaluation + quality gate trước khi active.
- Không trả lời khi thiếu căn cứ trong tài liệu (refusal + citation bắt buộc).
- Mọi số liệu thực nghiệm là số liệu thật, đo qua stack thật (Qdrant/Postgres/LiteLLM/Gemini) — không bịa; kết quả tiêu cực được ghi lại trung thực, không giấu (xem `docs/system/experiments/`).
- Không commit secret; `.env` nằm ngoài git.
