"""Health endpoints — contract: docs/system/contracts/api_contracts.md (Admin/Health API).

GET /health              -> liveness of the API itself.
GET /health/dependencies -> reachability of Qdrant, Postgres, Valkey, LiteLLM, Langfuse.
Dependency checks never raise: each reports ok | unreachable | not_configured.
"""

import asyncio
from datetime import UTC, datetime
from typing import Literal

import httpx
import psycopg
import redis.asyncio as aioredis
from fastapi import APIRouter

from src.common.config_loader import active_config_ids
from src.common.settings import APP_NAME, APP_VERSION, get_settings

router = APIRouter(tags=["health"])

DependencyStatus = Literal["ok", "unreachable", "not_configured"]
_PROBE_TIMEOUT = 3.0


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "env": settings.app_env,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _probe_http(url: str) -> DependencyStatus:
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT) as client:
            resp = await client.get(url)
        return "ok" if resp.status_code < 500 else "unreachable"
    except httpx.HTTPError:
        return "unreachable"


async def _probe_postgres(dsn: str, password_set: bool) -> DependencyStatus:
    if not password_set:
        return "not_configured"
    try:
        conn = await psycopg.AsyncConnection.connect(dsn, connect_timeout=int(_PROBE_TIMEOUT))
        await conn.close()
        return "ok"
    except psycopg.Error:
        return "unreachable"


async def _probe_valkey(url: str) -> DependencyStatus:
    client = aioredis.from_url(url, socket_connect_timeout=_PROBE_TIMEOUT)
    try:
        await client.ping()
        return "ok"
    except (aioredis.RedisError, OSError):
        return "unreachable"
    finally:
        await client.aclose()


@router.get("/health/dependencies")
async def health_dependencies() -> dict:
    settings = get_settings()

    qdrant, postgres, valkey, litellm, langfuse = await asyncio.gather(
        _probe_http(f"{settings.qdrant_url}/readyz"),
        _probe_postgres(settings.postgres_dsn, bool(settings.postgres_password)),
        _probe_valkey(settings.valkey_url),
        _probe_http(f"{settings.litellm_base_url}/health/liveliness"),
        _probe_http(f"{settings.langfuse_host}/api/public/health"),
    )

    services: dict[str, DependencyStatus] = {
        "qdrant": qdrant,
        "postgres": postgres,
        "valkey": valkey,
        "litellm": litellm,
        "langfuse": langfuse,
    }
    return {
        "status": "ok" if all(s != "unreachable" for s in services.values()) else "degraded",
        "services": services,
        "configs": active_config_ids(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
