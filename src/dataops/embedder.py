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


def _clients() -> list[genai.Client]:
    """Primary key + optional GEMINI_API_KEY_2 fallback.

    The free-tier DAILY quota (1000 request-items/project, measured
    2026-07-11 — see CHECKLIST Phase 4 "Chưa tốt") exhausts mid-workload;
    a second key from a different Google project has its own budget, so
    on 429 the next key is tried before backing off.
    """
    keys = [os.environ.get("GEMINI_API_KEY", ""), os.environ.get("GEMINI_API_KEY_2", "")]
    clients = [genai.Client(api_key=k) for k in keys if k]
    if not clients:
        raise EmbeddingError("GEMINI_API_KEY not set (check .env is loaded into environment)")
    return clients


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

    clients = _clients()
    config = types.EmbedContentConfig(
        output_dimensionality=output_dimensionality, task_type=task_type
    )
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        for i, client in enumerate(clients):
            try:
                resp = client.models.embed_content(model=model, contents=texts, config=config)
                return [e.values for e in resp.embeddings]
            except (ClientError, ServerError) as exc:
                last_exc = exc
                is_quota = "RESOURCE_EXHAUSTED" in str(exc)
                if is_quota and i + 1 < len(clients):
                    print(f"    [embed] key {i + 1} quota-limited, thu key {i + 2}")
                    continue  # thử ngay key kế tiếp, không chờ
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
