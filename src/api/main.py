"""FastAPI application entrypoint.

Phase 1: health endpoints. Phase 5: QA endpoints (/qa/query, /qa/debug,
/qa/traces). Phase 10: GET /metrics (Prometheus scrape) + Langfuse
tracing wired into RagService (src/rag/service.py, src/observability/).
Ingest/eval/feedback routers are added in their own phases — see
docs/system/CHECKLIST_IMPLEMENTATION.md.

Run local:  uvicorn src.api.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health, metrics, prompts, qa
from src.common.settings import APP_VERSION, get_settings

# Phase 10 (frontend showcase, thêm sớm 2026-07-12): Next.js chạy khác
# origin (localhost:3000) với API (localhost:8000) — browser chặn fetch
# cross-origin nếu thiếu CORS. Danh sách cố định cho dev + Vercel preview
# domain mẫu; KHÔNG dùng "*" vì QA endpoint không phải public/anonymous
# read-only mãi mãi (Phase 9 sẽ thêm auth/rate-limit).
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    app = FastAPI(
        title="viRAGops — Vietnamese Document QA (IUH)",
        description=(
            "RAG QA API with full LLMOps/RAGOps lifecycle: data versioning, "
            "retrieval experiments, PromptOps, evaluation, quality gate, "
            "observability, optimization and feedback loop."
        ),
        version=APP_VERSION,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(qa.router)
    app.include_router(prompts.router)
    app.include_router(metrics.router)
    return app


app = create_app()
