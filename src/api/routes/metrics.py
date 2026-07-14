"""GET /metrics — Prometheus scrape endpoint (Phase 10, Module 7).

Metric definitions live in src/observability/metrics.py, updated inline
by RagService.answer() (src/rag/service.py) via
obs_metrics.record_request() — this route only exposes the default
prometheus_client registry, it never computes anything itself.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
