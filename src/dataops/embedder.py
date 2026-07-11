"""Dense embedding via Gemini API (config/model_gateway.yaml route "embedding").

Real free-tier quota measured 2026-07-11 (see model_gateway.yaml comments):
"EmbedContentRequestsPerMinutePerUserPerProjectPerModel-FreeTier",
quotaValue=100 — each text in a batch call counts as one request against
this per-minute quota, not one call = one request. A batch of 100 filled
the quota in a single call. `embed_batch` therefore caps batch size
(default 80, from config/ingest.yaml) and sleeps between batches, plus
retries with the server-suggested delay on 429.
"""

from __future__ import annotations

import os
import re
import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

_RETRY_DELAY_RE = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


class EmbeddingError(RuntimeError):
    pass


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise EmbeddingError("GEMINI_API_KEY not set (check .env is loaded into environment)")
    return genai.Client(api_key=api_key)


def _extract_retry_delay(exc: Exception, default: float) -> float:
    m = _RETRY_DELAY_RE.search(str(exc))
    return float(m.group(1)) + 2.0 if m else default


def embed_batch(
    texts: list[str],
    model: str,
    task_type: str,
    output_dimensionality: int = 768,
    max_retries: int = 4,
) -> list[list[float]]:
    """Embed one batch (<= ~80 texts, see module docstring) in a single API call."""
    if not texts:
        return []

    client = _client()
    config = types.EmbedContentConfig(
        output_dimensionality=output_dimensionality, task_type=task_type
    )
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.models.embed_content(model=model, contents=texts, config=config)
            return [e.values for e in resp.embeddings]
        except (ClientError, ServerError) as exc:
            last_exc = exc
            wait = _extract_retry_delay(exc, default=10.0 * (attempt + 1))
            print(f"    [embed retry {attempt + 1}/{max_retries}] {type(exc).__name__}: "
                  f"wait {wait:.1f}s")
            time.sleep(wait)
    raise EmbeddingError(f"embed_batch failed after {max_retries} retries") from last_exc


def embed_all(
    texts: list[str],
    model: str,
    task_type: str,
    output_dimensionality: int,
    batch_size: int,
    batch_delay_seconds: float,
    progress_label: str = "embed",
) -> list[list[float]]:
    """Embed an arbitrary number of texts, chunked into rate-limit-safe batches."""
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        print(f"  [{progress_label}] batch {start}-{start + len(batch)}/{len(texts)}")
        vectors.extend(
            embed_batch(batch, model=model, task_type=task_type, output_dimensionality=output_dimensionality)
        )
        if start + batch_size < len(texts):
            time.sleep(batch_delay_seconds)
    return vectors
