"""FastAPI application entrypoint.

Phase 1: health endpoints. Phase 5: QA endpoints (/qa/query, /qa/debug,
/qa/traces). Ingest/eval/feedback routers are added in their own phases —
see docs/system/CHECKLIST_IMPLEMENTATION.md.

Run local:  uvicorn src.api.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI

from src.api.routes import health, prompts, qa
from src.common.settings import APP_VERSION, get_settings


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
    app.include_router(health.router)
    app.include_router(qa.router)
    app.include_router(prompts.router)
    return app


app = create_app()
