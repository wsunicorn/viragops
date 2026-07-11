"""Minimal model-gateway client for the RAG runtime (Phase 5).

The runtime never names a provider/model — it asks for a TIER
(cheap/balanced/strong/judge) and this client resolves primary/fallback
from config/model_gateway.yaml. Phase 7 swaps the transport to LiteLLM
behind the same `generate()` interface; nothing in the runtime changes.

JSON mode: Gemini's `response_mime_type="application/json"` is requested
so the QA prompt's strict-JSON output contract doesn't depend on the
model resisting markdown fences (the citation parser still strips fences
defensively for other providers later).

`MockGateway` implements the same interface for unit/integration tests —
no network, deterministic output.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATEWAY_CONFIG = PROJECT_ROOT / "config" / "model_gateway.yaml"


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class GatewayError(RuntimeError):
    pass


class Gateway(Protocol):
    def generate(self, tier: str, prompt: str, json_output: bool = True) -> GenerationResult: ...


class GeminiGateway:
    def __init__(self, config_path: Path | None = None, max_retries: int = 2) -> None:
        cfg = yaml.safe_load((config_path or GATEWAY_CONFIG).read_text(encoding="utf-8"))
        self._routes = cfg["routes"]
        self._timeout = cfg.get("default_timeout_seconds", 30)
        self._max_retries = max_retries
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise GatewayError("GEMINI_API_KEY not set")
        from google import genai  # import muộn: unit test dùng MockGateway không cần SDK

        self._client = genai.Client(api_key=api_key)

    def generate(self, tier: str, prompt: str, json_output: bool = True) -> GenerationResult:
        from google.genai import types
        from google.genai.errors import ClientError, ServerError

        route = self._routes[tier]
        models = [route["primary"]["model"], route["fallback"]["model"]]
        config = types.GenerateContentConfig(
            response_mime_type="application/json" if json_output else None,
        )

        last_exc: Exception | None = None
        for model in dict.fromkeys(models):  # dedupe, giữ thứ tự primary->fallback
            for attempt in range(self._max_retries):
                t0 = time.perf_counter()
                try:
                    resp = self._client.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                    if not resp.text or not resp.text.strip():
                        raise GatewayError(
                            f"empty response, finish_reason="
                            f"{resp.candidates[0].finish_reason if resp.candidates else 'NONE'}"
                        )
                    usage = resp.usage_metadata
                    return GenerationResult(
                        text=resp.text,
                        provider="gemini",
                        model=model,
                        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                    )
                except (ClientError, ServerError, GatewayError) as exc:
                    last_exc = exc
                    wait = 5.0 * (attempt + 1)
                    print(f"    [gateway {model} retry {attempt + 1}/{self._max_retries}] "
                          f"{type(exc).__name__}: {str(exc)[:120]}, wait {wait:.0f}s")
                    time.sleep(wait)
        raise GatewayError(f"all models failed for tier '{tier}'") from last_exc


class MockGateway:
    """Deterministic gateway for tests: echoes a canned JSON answer citing
    the first chunk_id it finds in the prompt (mimicking a grounded model)."""

    def __init__(self, refuse: bool = False) -> None:
        self.refuse = refuse
        self.last_prompt: str | None = None

    def generate(self, tier: str, prompt: str, json_output: bool = True) -> GenerationResult:
        import json
        import re

        self.last_prompt = prompt
        if self.refuse:
            payload = {"answer": "", "citations": [], "refusal": True}
        else:
            chunk_ids = re.findall(r"\[(chunk_[\w]+)\]", prompt)
            payload = {
                "answer": "Câu trả lời mô phỏng từ ngữ cảnh.",
                "citations": [{"chunk_id": cid} for cid in chunk_ids[:1]],
                "refusal": False,
            }
        return GenerationResult(
            text=json.dumps(payload, ensure_ascii=False),
            provider="mock",
            model=f"mock-{tier}",
            input_tokens=len(prompt) // 4,
            output_tokens=50,
            latency_ms=1,
        )
