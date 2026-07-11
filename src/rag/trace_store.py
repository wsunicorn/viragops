"""Basic trace store for Phase 5 — schema follows contracts/data_schemas.md.

Two sinks, both intentionally simple:
- in-memory ring buffer serving `GET /qa/traces/{trace_id}` immediately;
- JSONL append (`data/traces/traces.jsonl`) so traces survive restarts
  and can be analyzed offline before Langfuse arrives in Phase 10 (which
  replaces this module's transport, not its call sites).

Not thread-safe beyond CPython append atomicity — acceptable for a
single-process dev server; noted for Phase 10.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACES_PATH = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"

_MAX_IN_MEMORY = 500


def new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"


class TraceStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or TRACES_PATH
        self._recent: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def record(self, trace: dict[str, Any]) -> None:
        trace.setdefault("created_at", datetime.now(UTC).isoformat())
        self._recent[trace["trace_id"]] = trace
        while len(self._recent) > _MAX_IN_MEMORY:
            self._recent.popitem(last=False)

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

    def get(self, trace_id: str) -> dict[str, Any] | None:
        return self._recent.get(trace_id)
