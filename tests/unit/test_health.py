"""Unit tests for health endpoints (Phase 1 Definition of Done)."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.common.settings import APP_NAME, APP_VERSION

client = TestClient(app)

ALLOWED_STATUSES = {"ok", "unreachable", "not_configured"}


def test_health_returns_200_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == APP_VERSION
    assert body["service"] == APP_NAME
    assert "timestamp" in body


def test_health_dependencies_reports_all_services():
    resp = client.get("/health/dependencies")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["services"].keys()) == {"qdrant", "postgres", "valkey", "litellm", "langfuse"}
    for name, status in body["services"].items():
        assert status in ALLOWED_STATUSES, f"{name} has invalid status {status}"
    # Dependency probe must never crash the endpoint, even with nothing running.
    assert body["status"] in {"ok", "degraded"}
