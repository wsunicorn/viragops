"""LLM-based listwise reranker via Gemini (Phase 4).

Why not bge-reranker-v2-m3 (the model named in config/retrieval.yaml)?
Downloading it from huggingface.co hits the same ISP-level CDN reset
already documented for fastembed in Phase 3 (see pyproject.toml comment)
— a ~2GB cross-encoder download is not currently feasible on this
connection. A Gemini listwise rerank is the pragmatic substitute: one
API call per query (not per query-chunk pair), using the "cheap" tier
route (gemini-3.1-flash-lite) from config/model_gateway.yaml.

Trade-offs, stated honestly for the experiment report:
- adds ~1-2s latency per query and consumes free-tier quota (~10 RPM),
  so experiments only enable it for a subset of configs;
- non-deterministic (LLM output) — unlike a cross-encoder, two runs may
  order borderline candidates differently;
- output parsing is defensive: any candidate the model forgets to rank
  is appended in original retrieval order, so reranking can never LOSE
  a candidate, only reorder.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

import yaml
from google import genai
from google.genai.errors import ClientError, ServerError

from src.dataops.vietnamese_normalizer import collapse_whitespace

_EXCERPT_CHARS = 600

_PROMPT = (
    "Bạn là bộ xếp hạng đoạn văn cho hệ thống hỏi đáp quy chế đại học.\n"
    "Câu hỏi: {question}\n\n"
    "Dưới đây là {n} đoạn văn đánh số từ 1 đến {n}. Hãy xếp hạng chúng theo mức độ "
    "chứa thông tin trả lời trực tiếp câu hỏi, giảm dần.\n"
    "CHỈ trả về danh sách số thứ tự cách nhau bằng dấu phẩy, ví dụ: 3,1,2. "
    "Không giải thích.\n\n{passages}"
)


def _load_cheap_model(gateway_config_path: str) -> str:
    cfg = yaml.safe_load(open(gateway_config_path, encoding="utf-8"))
    return cfg["routes"]["cheap"]["primary"]["model"]


class GeminiListwiseReranker:
    def __init__(self, gateway_config_path: str, max_retries: int = 3) -> None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self._client = genai.Client(api_key=api_key)
        self._model = _load_cheap_model(gateway_config_path)
        self._max_retries = max_retries

    def rerank(self, question: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(candidates) <= 1:
            return candidates

        passages = "\n\n".join(
            f"[{i + 1}] {collapse_whitespace(c['text'])[:_EXCERPT_CHARS]}"
            for i, c in enumerate(candidates)
        )
        prompt = _PROMPT.format(question=question, n=len(candidates), passages=passages)

        text = ""
        for attempt in range(self._max_retries):
            try:
                resp = self._client.models.generate_content(model=self._model, contents=prompt)
                text = resp.text or ""
                break
            except (ClientError, ServerError) as exc:
                wait = 10.0 * (attempt + 1)
                print(f"    [rerank retry {attempt + 1}/{self._max_retries}] "
                      f"{type(exc).__name__}, wait {wait:.0f}s")
                time.sleep(wait)
        if not text:
            return candidates  # rerank failed -> keep retrieval order, never drop results

        order: list[int] = []
        for tok in re.findall(r"\d+", text):
            idx = int(tok) - 1
            if 0 <= idx < len(candidates) and idx not in order:
                order.append(idx)
        for idx in range(len(candidates)):  # anything unranked keeps original order at the tail
            if idx not in order:
                order.append(idx)
        return [candidates[i] for i in order]
