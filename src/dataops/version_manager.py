"""data_version / index_version helpers (config/README.md versioning convention).

| Artifact | Format          | Ví dụ            |
|----------|-----------------|------------------|
| Data     | data_YYYYMMDD   | data_20260711    |
| Index    | idx_<data>_<embedding> | idx_20260711_gemini_embed001 |

Versions only ever increase — re-ingesting the same day re-runs the same
version (idempotent by design for local dev), a new day produces a new one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


def make_data_version(today: datetime | None = None) -> str:
    d = today or datetime.now(UTC)
    return f"data_{d.strftime('%Y%m%d')}"


def make_index_version(data_version: str, embedding_model: str) -> str:
    slug = embedding_model.replace("-", "").replace(".", "").replace("_", "")
    return f"idx_{data_version.removeprefix('data_')}_{slug}"


@dataclass
class IngestManifest:
    data_version: str
    index_version: str
    ingest_config_id: str
    source_snapshot: str
    chunking_strategy_indexed: str
    embedding_model: str
    embedding_output_dimensionality: int
    sparse_provider: str
    qdrant_collection: str
    document_count: int
    chunk_count: int
    chunk_counts_by_strategy: dict[str, int]
    quality_report: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_manifest(**kwargs: Any) -> IngestManifest:
    kwargs.setdefault("created_at", datetime.now(UTC).isoformat())
    return IngestManifest(**kwargs)
