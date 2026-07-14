"""QA request/response schemas — contract: docs/system/contracts/api_contracts.md.

Field names and shapes mirror the contract exactly so the thesis report
can show contract-vs-implementation side by side. `mode` maps 1:1 to a
model-gateway tier (config/model_gateway.yaml routes).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# "auto" (Phase 11): RagService resolves the real tier via
# src/optimization/routing.py::resolve_tier() based on query complexity —
# ModelInfo.routing_policy reports the resolved tier, not "auto" itself.
Mode = Literal["cheap", "balanced", "strong", "auto"]


class QARequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str | None = None
    user_id: str = "anonymous"
    domain: str = "university_regulation"
    mode: Mode = "balanced"
    debug: bool = False


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    section: str | None = None
    page: int | None = None
    quote: str | None = None


class ModelInfo(BaseModel):
    provider: str
    model: str
    routing_policy: str


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


class QAResponse(BaseModel):
    request_id: str
    trace_id: str
    answer: str
    citations: list[Citation]
    # Heuristic có căn cứ (src/rag/confidence.py), KHÔNG phải xác suất
    # calibrate qua ground-truth correctness. None khi refusal=True.
    confidence: float | None = None
    refusal: bool
    model: ModelInfo
    usage: Usage


class RetrievedChunkDebug(BaseModel):
    chunk_id: str
    score: float
    section: str | None = None
    document_id: str
    text_preview: str


class QADebugResponse(QAResponse):
    retrieved_chunks: list[RetrievedChunkDebug]
    prompt_version: str
    retrieval_config_id: str
    data_version: str | None
    index_version: str | None
