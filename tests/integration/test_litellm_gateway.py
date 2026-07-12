"""Integration test cho LiteLLMGateway (Phase 7) — proxy THẬT (docker
compose `litellm`), gọi Gemini thật qua route `cheap-primary`.

Tự skip khi proxy chưa chạy. Không test fallback-tới-Ollama ở đây (đã
verify thủ công bằng container cô lập với key giả — xem CHECKLIST Phase 7
"Chưa tốt": chưa có cách tự động hoá test này mà không đụng key thật của
service đang chạy).
"""

from __future__ import annotations

import os

import httpx
import pytest

from src.rag.gateway_client import GatewayError
from src.rag.litellm_gateway import LiteLLMGateway

BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")


def _proxy_ready() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health/liveliness", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _proxy_ready() or not os.environ.get("LITELLM_MASTER_KEY"),
    reason="LiteLLM proxy not running or LITELLM_MASTER_KEY not set in this shell",
)


@pytest.fixture(scope="module")
def gateway() -> LiteLLMGateway:
    master_key = os.environ.get("LITELLM_MASTER_KEY", "")
    return LiteLLMGateway(base_url=BASE_URL, master_key=master_key)


def test_cheap_tier_real_call_hits_primary(gateway):
    result = gateway.generate(tier="cheap", prompt="Say hi in exactly two words.")
    assert result.text.strip()
    assert result.provider == "litellm"
    assert result.fallback_hop == "primary"
    assert result.attempted_fallbacks == 0
    assert result.input_tokens > 0
    assert result.output_tokens > 0
    assert result.latency_ms > 0


def test_json_output_mode_produces_parseable_json(gateway):
    result = gateway.generate(
        tier="cheap",
        prompt='Return exactly this JSON, nothing else: {"answer": "ok", "citations": [], "refusal": false}',
        json_output=True,
    )
    import json

    parsed = json.loads(result.text)
    assert parsed["refusal"] is False


def test_unreachable_proxy_raises_gateway_error():
    bad_gateway = LiteLLMGateway(base_url="http://localhost:1", master_key="x", timeout=2.0)
    with pytest.raises(GatewayError):
        bad_gateway.generate(tier="cheap", prompt="hi")
