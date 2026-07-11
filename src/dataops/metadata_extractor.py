"""Build the Document registry for Phase 3 ingest (data_schemas.md "Document schema").

Reuses `DOCS` from scripts/seed_golden_set_iuh.py as the single source of
truth for which document_id maps to which processed .txt file — the golden
set's `expected_citations[].document_id` values MUST match what gets
indexed, or citation-accuracy eval in Phase 5+ is meaningless by
construction. `processed_manifest.json` supplies char_count/sha256 for
freshness checks.

Only these 9 curated documents are ingested by default (see
docs/system/experiments/golden_set_review.md and data_sources_iuh.md):
several other extracted files (D2, D7, D9-index, D10, D11 shell pages) are
mostly pdt.iuh.edu.vn/stsv.iuh.edu.vn SPA app-shell noise with almost no
real regulation text (verified by reading them directly) — indexing them
would pollute retrieval with site-chrome chunks instead of adding real
coverage, so they are intentionally excluded rather than padded in to hit
a document count.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_SCRIPT = PROJECT_ROOT / "scripts" / "seed_golden_set_iuh.py"

# Known effective dates / source URLs, cross-checked in
# docs/system/experiments/golden_set_review.md's document registry table.
# Left as None where the source itself has no confirmed decision number/date
# (documented there as a genuine, not a crawl, gap) — never guessed.
_EFFECTIVE_DATE: dict[str, str | None] = {
    "doc_qd1482_quy_che_tin_chi": "2021-11-15",
    "doc_qd610_thi_danh_gia": "2025-02-21",
    "doc_tqa_phuc_khao": "2025-02-21",
    "doc_camnang_dieu_kien_tot_nghiep": None,
    "doc_camnang_chuan_tieng_anh": None,
    "doc_camnang_bang_quy_doi_tieng_anh": None,
    "doc_hd05_mien_giam_hp": "2025-09-18",
    "doc_sotay_2024": None,
    "doc_faet_hoc_bong_2024": None,
}

_SOURCE_URI: dict[str, str] = {
    "doc_qd1482_quy_che_tin_chi": "https://camnang.iuh.edu.vn/quy-che-dao-tao-theo-he-thong-tin-chi.php",
    "doc_qd610_thi_danh_gia": "https://tqa.iuh.edu.vn/wp-content/uploads/2025/12/Quyet-dinh-so-610-QD-DHCN.pdf",
    "doc_tqa_phuc_khao": "https://tqa.iuh.edu.vn/cong-tac-khao-thi/quy-dinh-phuc-khao/",
    "doc_camnang_dieu_kien_tot_nghiep": "https://camnang.iuh.edu.vn/dieu-kien-xet-tot-nghiep.php",
    "doc_camnang_chuan_tieng_anh": "https://camnang.iuh.edu.vn/quy-dinh-chuan-tieng-anh.php",
    "doc_camnang_bang_quy_doi_tieng_anh": "https://camnang.iuh.edu.vn/bang-quy-doi-diem-chung-chi-tieng-anh.php",
    "doc_hd05_mien_giam_hp": "https://ctsv.iuh.edu.vn/",
    "doc_sotay_2024": "https://tqa.iuh.edu.vn/thong-bao/so-tay-sinh-vien-cua-iuh-nam-2024/",
    "doc_faet_hoc_bong_2024": "https://faet.iuh.edu.vn/news.html@detail@271@585@",
}


@dataclass
class DocumentRecord:
    document_id: str
    domain: str
    title: str
    source_uri: str
    source_type: str
    source_version: str
    effective_date: str | None
    ingested_at: str
    text: str
    char_count: int
    sha256: str
    metadata: dict[str, Any]


def _load_docs_registry() -> dict[str, dict[str, str]]:
    """Import DOCS from scripts/seed_golden_set_iuh.py without turning
    scripts/ into a package — it's a script, not a library, by convention
    in this repo (see scripts/*.py header docstrings)."""
    spec = importlib.util.spec_from_file_location("seed_golden_set_iuh", SEED_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.DOCS


def load_documents(processed_dir: Path, source_version: str) -> list[DocumentRecord]:
    """Load the curated document set, reading actual .txt content from disk
    so callers (chunker) never re-open files themselves."""
    docs_registry = _load_docs_registry()
    manifest_path = processed_dir / "processed_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest_by_file = {d["txt_file"]: d for d in manifest.get("documents", []) if d.get("txt_file")}

    now = datetime.now(UTC).isoformat()
    records: list[DocumentRecord] = []
    for document_id, info in docs_registry.items():
        txt_path = processed_dir / info["source_file"]
        if not txt_path.exists():
            raise FileNotFoundError(f"{document_id}: missing {txt_path}")
        text = txt_path.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        manifest_entry = manifest_by_file.get(info["source_file"], {})

        records.append(
            DocumentRecord(
                document_id=document_id,
                domain="university_regulation",
                title=info["title"],
                source_uri=_SOURCE_URI.get(document_id, ""),
                source_type="pdf" if manifest_entry.get("ocr_applied") else "html",
                source_version=source_version,
                effective_date=_EFFECTIVE_DATE.get(document_id),
                ingested_at=now,
                text=text,
                char_count=len(text),
                sha256=sha256,
                metadata={
                    "owner": "iuh",
                    "language": "vi",
                    "ocr_applied": bool(manifest_entry.get("ocr_applied", False)),
                    "source_file": info["source_file"],
                },
            )
        )
    return records
