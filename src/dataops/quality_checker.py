"""Chunk-level data quality checks for Phase 3 (Module 1 DataOps/RAGOps).

Per docs/system/modules/01_data_ragops.md acceptance criteria: "Data
quality report không có lỗi critical." Checks are split into `critical`
(block ingest — something is actually broken) and `warning` (flagged in
the report but does not stop the pipeline — e.g. an unusually short chunk
from a genuinely short Điều).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QualityReport:
    total_chunks: int
    critical_errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_critical_clean(self) -> bool:
        return not self.critical_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_chunks": self.total_chunks,
            "critical_error_count": len(self.critical_errors),
            "warning_count": len(self.warnings),
            "critical_errors": self.critical_errors,
            "warnings": self.warnings,
        }


def check_chunks(
    chunks: list[dict[str, Any]],
    min_tokens: int = 15,
    max_tokens: int = 1200,
) -> QualityReport:
    """`chunks` is a list of fully-assembled chunk dicts (chunk_id,
    document_id, text, token_count, section, ... — the shape written to
    data/chunks/*.jsonl by scripts/ingest_data.py), not raw chunker output.
    """
    report = QualityReport(total_chunks=len(chunks))

    seen_ids: set[str] = set()
    text_hashes: dict[str, list[str]] = {}

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "<missing>")

        # --- critical: empty text ---
        text = chunk.get("text", "")
        if not text or not text.strip():
            report.critical_errors.append({"chunk_id": chunk_id, "error": "empty_text"})
            continue

        # --- critical: missing document_id ---
        if not chunk.get("document_id"):
            report.critical_errors.append({"chunk_id": chunk_id, "error": "missing_document_id"})

        # --- critical: missing section (every chunk should be traceable to
        # some part of the source, even if it's a paragraph-fallback label) ---
        if chunk.get("section") is None and chunk.get("chunking_strategy") not in (
            "fixed",
            "recursive",
        ):
            # fixed/recursive strategies never carry a section label by
            # design (see chunker.py) — only flag structure_aware/
            # parent_child chunks that unexpectedly have no section.
            report.warnings.append({"chunk_id": chunk_id, "warning": "missing_section"})

        # --- critical: duplicate chunk_id ---
        if chunk_id in seen_ids:
            report.critical_errors.append({"chunk_id": chunk_id, "error": "duplicate_chunk_id"})
        seen_ids.add(chunk_id)

        # --- warning: duplicate content across chunks (dedup candidates) ---
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        text_hashes.setdefault(h, []).append(chunk_id)

        # --- warning: chunk length out of configured band ---
        token_count = chunk.get("token_count", 0)
        if token_count < min_tokens:
            report.warnings.append(
                {"chunk_id": chunk_id, "warning": "chunk_too_short", "token_count": token_count}
            )
        elif token_count > max_tokens:
            report.warnings.append(
                {"chunk_id": chunk_id, "warning": "chunk_too_long", "token_count": token_count}
            )

    for ids in text_hashes.values():
        if len(ids) > 1:
            report.warnings.append({"warning": "duplicate_content", "chunk_ids": ids})

    return report


def summarize_by_document(chunks: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(c.get("document_id", "<missing>") for c in chunks))
