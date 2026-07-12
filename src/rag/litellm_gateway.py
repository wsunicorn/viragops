"""LiteLLM-backed gateway (Phase 7) — implements the same `Gateway`
protocol as gateway_client.py's GeminiGateway, so src/rag/service.py
doesn't change at all when swapping transport (that was the whole point
of separating the interface in Phase 5).

Runtime now calls the LiteLLM PROXY over HTTP (OpenAI-compatible
`/chat/completions`) instead of the Gemini SDK directly — the proxy
(config/litellm_config.yaml, docker-compose `litellm` service) owns
provider selection, ordered fallback (Gemini primary -> Gemini secondary
key -> local Ollama), timeout and retry policy. This module is a thin,
protocol-shaped HTTP client; it does not itself decide providers.

Request model name = f"{tier}-primary" — the proxy config's fallback
chain (not this code) decides what actually serves the request. The
response's `model` field tells us which deployment really answered
(useful for the trace: "was this Gemini or the Ollama fallback").
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import httpx

from src.rag.gateway_client import GatewayError, GenerationResult

_HOP_BY_SUFFIX = {"-primary": "primary", "-secondary": "secondary", "-local": "local"}


def _classify_hop(model_group: str) -> str:
    for suffix, hop in _HOP_BY_SUFFIX.items():
        if model_group.endswith(suffix):
            return hop
    return "unknown"


@dataclass
class LiteLLMResult(GenerationResult):
    """GenerationResult + gateway-specific fields read from LiteLLM proxy
    response headers (x-litellm-*) — real fallback hop and estimated cost,
    not guessed from the response body."""

    fallback_hop: str = "unknown"
    attempted_fallbacks: int = 0
    cost_usd: float = 0.0
    extra: dict = field(default_factory=dict)


class LiteLLMGateway:
    def __init__(self, base_url: str | None = None, master_key: str | None = None,
                 timeout: float = 35.0) -> None:
        self._base_url = (base_url or os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")).rstrip("/")
        self._master_key = master_key or os.environ.get("LITELLM_MASTER_KEY", "")
        self._timeout = timeout

    def generate(self, tier: str, prompt: str, json_output: bool = True) -> LiteLLMResult:
        payload = {
            "model": f"{tier}-primary",
            "messages": [{"role": "user", "content": prompt}],
        }
        if json_output:
            # Nếu deployment đang phục vụ không hỗ trợ response_format,
            # litellm_settings.drop_params:true (litellm_config.yaml) sẽ
            # bỏ qua field này thay vì lỗi cứng — prompt vẫn tự yêu cầu
            # JSON bằng text nên vẫn có cơ chế dự phòng.
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self._master_key}"} if self._master_key else {}

        t0 = time.perf_counter()
        try:
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                json=payload, headers=headers, timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise GatewayError(f"litellm proxy unreachable: {exc}") from exc
        latency_ms = int((time.perf_counter() - t0) * 1000)

        if resp.status_code != 200:
            raise GatewayError(f"litellm proxy error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content", "")
        if not content or not content.strip():
            raise GatewayError("litellm proxy returned empty content (all fallback hops exhausted?)")

        usage = data.get("usage") or {}
        # x-litellm-model-group = model_name mà THỰC SỰ phục vụ request (vd
        # "cheap-local" nếu đã rơi hết xuống fallback cuối) — đáng tin hơn
        # field "model" trong body, vốn không nhất quán giữa hit-primary
        # (trả về model_name yêu cầu) và đã-fallback (trả về chuỗi
        # provider/model gốc, vd "ollama_chat/qwen2.5:7b"). Đo thật 2026-07-12.
        model_group = resp.headers.get("x-litellm-model-group", f"{tier}-primary")

        return LiteLLMResult(
            text=content,
            provider="litellm",
            model=data.get("model", model_group),
            input_tokens=usage.get("prompt_tokens", 0) or 0,
            output_tokens=usage.get("completion_tokens", 0) or 0,
            latency_ms=latency_ms,
            fallback_hop=_classify_hop(model_group),
            attempted_fallbacks=int(resp.headers.get("x-litellm-attempted-fallbacks", 0) or 0),
            cost_usd=float(resp.headers.get("x-litellm-response-cost", 0.0) or 0.0),
            extra={"model_group": model_group},
        )
