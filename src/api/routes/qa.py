"""QA endpoints — contract: docs/system/contracts/api_contracts.md (QA API).

POST /qa/query          — hỏi đáp một câu (answer + citations + trace_id).
POST /qa/debug          — như /qa/query nhưng trả thêm retrieved chunks +
                          version metadata (admin/dev; KHÔNG trả prompt nội
                          dung đầy đủ — chỉ prompt_version).
GET  /qa/traces/{id}    — trace cơ bản của 1 request (in-memory window).

/qa/stream (contract) chưa implement — lý do ghi ở CHECKLIST Phase 5
"Chưa tốt": gateway hiện chưa hỗ trợ streaming, để Phase 7 (LiteLLM).

RagService được khởi tạo lười (lần request đầu) thay vì lúc import — app
vẫn khởi động/healthcheck được khi Qdrant chưa bật, đúng tinh thần
/health/dependencies "not_configured/unreachable" thay vì crash.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from src.common.settings import get_settings
from src.observability.tracing import make_langfuse_client
from src.rag.litellm_gateway import LiteLLMGateway
from src.rag.prompt_builder import RegistryPromptProvider
from src.rag.schemas import QADebugResponse, QARequest, QAResponse
from src.rag.service import RagService

router = APIRouter(prefix="/qa", tags=["qa"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_service() -> RagService:
    settings = get_settings()
    # Phase 7: runtime không còn gọi thẳng Gemini SDK (GeminiGateway, Phase
    # 5) — mọi model call đi qua LiteLLM proxy (docker-compose `litellm`,
    # config/litellm_config.yaml), có routing/fallback/budget thật.
    return RagService(
        gateway=LiteLLMGateway(base_url=settings.litellm_base_url, master_key=settings.litellm_master_key),
        qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
        # Phase 10: None nếu thiếu key/SDK — service.py fail-open, request
        # vẫn chạy bình thường không có tracing (xem src/observability/tracing.py).
        langfuse=make_langfuse_client(
            settings.langfuse_host, settings.langfuse_public_key, settings.langfuse_secret_key
        ),
    )


async def _answer(req: QARequest) -> QAResponse | QADebugResponse:
    try:
        service = get_service()
    except Exception as exc:  # noqa: BLE001 - thiếu index/manifest/key -> 503 rõ ràng
        logger.exception("RagService init failed")
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "SERVICE_UNAVAILABLE",
                "message": "RAG runtime chưa sẵn sàng (kiểm tra Qdrant/ingest manifest/API key).",
                "details": {"reason": str(exc)[:200]},
            },
        ) from exc
    # service.answer là sync (SDK google-genai sync) -> chạy trong threadpool
    # để không chặn event loop của FastAPI.
    return await asyncio.to_thread(service.answer, req)


@router.post("/query", response_model=QAResponse, response_model_exclude_none=False)
async def qa_query(req: QARequest) -> QAResponse:
    req.debug = False
    return await _answer(req)


@router.post("/debug", response_model=QADebugResponse)
async def qa_debug(req: QARequest) -> QADebugResponse:
    req.debug = True
    return await _answer(req)


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> dict:
    try:
        service = get_service()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail={"error_code": "SERVICE_UNAVAILABLE"}) from exc
    trace = service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TRACE_NOT_FOUND",
                "message": f"Không tìm thấy trace {trace_id} trong cửa sổ gần nhất.",
            },
        )
    return trace
