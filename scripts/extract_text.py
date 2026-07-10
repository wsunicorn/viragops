"""Extract clean text from a raw IUH snapshot (Phase 2 -> feeds golden set drafting).

Reads data/raw/iuh/<snapshot>/manifest.json, extracts readable text from every
successfully downloaded HTML/PDF/DOCX file, and writes:
  - data/processed/iuh/<snapshot>/<same-stem>.txt   (one per source document)
  - data/processed/iuh/<snapshot>/processed_manifest.json (quality signals)

This is a lightweight Phase 2 utility to make raw HTML/PDF readable for
writing the golden set (docs/system/experiments/golden_set_design.md) — it is
NOT the full Module 1 DataOps pipeline (chunking/embedding/indexing, which
belongs to Phase 3, see docs/system/modules/01_data_ragops.md).

Flags documents that likely need OCR (PDF with near-zero extractable text per
page — typical of scanned documents) instead of guessing silently.

Usage:
    python scripts/extract_text.py --snapshot src_20260710
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "iuh"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "iuh"

# Tag thường là chrome (menu, footer, script) không mang nội dung quy chế —
# loại bỏ trước khi lấy text để giảm nhiễu cho việc viết câu hỏi/chunking.
NOISE_SELECTORS = [
    "script", "style", "nav", "footer", "header", "iframe", "noscript",
    ".menu", "#menu", ".navbar", ".breadcrumb", ".sidebar", ".footer", ".header",
]

MIN_CHARS_PER_PAGE_OCR_THRESHOLD = 40  # dưới ngưỡng này -> nghi ngờ PDF scan


def extract_html_text(content: bytes) -> tuple[str, str]:
    """Return (title, clean_text)."""
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    for sel in NOISE_SELECTORS:
        for tag in soup.select(sel):
            tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return title, "\n".join(lines)


def extract_pdf_text(path: Path) -> tuple[str, int, float]:
    """Return (text, page_count, avg_chars_per_page)."""
    reader = PdfReader(str(path))
    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - pypdf raises various parser errors on malformed PDFs
            pages_text.append("")
    text = "\n\n".join(pages_text)
    page_count = len(reader.pages)
    avg_chars = (len(text) / page_count) if page_count else 0.0
    return text, page_count, avg_chars


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def process_entry(entry: dict, snapshot_dir: Path, out_dir: Path) -> dict | None:
    if entry.get("status") != "ok" or "file" not in entry:
        return None

    src_path = snapshot_dir / entry["file"]
    if not src_path.exists():
        return {**entry, "extract_status": "source_missing"}

    ext = src_path.suffix.lower()
    stem = src_path.stem
    result = {
        "doc_id": entry.get("doc_id"),
        "title": entry.get("title", ""),
        "source_file": entry["file"],
        "url": entry.get("url"),
    }

    if ext == ".html":
        title, text = extract_html_text(src_path.read_bytes())
        result["title"] = result["title"] or title
        result["extract_method"] = "html"
        result["needs_ocr"] = False
    elif ext == ".pdf":
        text, page_count, avg_chars = extract_pdf_text(src_path)
        result["extract_method"] = "pdf"
        result["page_count"] = page_count
        result["avg_chars_per_page"] = round(avg_chars, 1)
        result["needs_ocr"] = avg_chars < MIN_CHARS_PER_PAGE_OCR_THRESHOLD
    else:
        # .docx và loại khác: chưa hỗ trợ trích xuất ở Phase 2, giữ nguyên file gốc.
        return {**result, "extract_status": "unsupported_format", "extract_method": ext}

    text = normalize_whitespace(text)
    txt_filename = f"{stem}.txt"
    (out_dir / txt_filename).write_text(text, encoding="utf-8")

    result.update(
        extract_status="ok",
        txt_file=txt_filename,
        char_count=len(text),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()

    snapshot_dir = RAW_DIR / args.snapshot
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir = PROCESSED_DIR / args.snapshot
    out_dir.mkdir(parents=True, exist_ok=True)

    all_entries = manifest.get("documents", []) + manifest.get("discovered_documents", [])
    results = []
    for entry in all_entries:
        r = process_entry(entry, snapshot_dir, out_dir)
        if r is None:
            continue
        results.append(r)
        status = r.get("extract_status", "?")
        flag = " [NEEDS OCR?]" if r.get("needs_ocr") else ""
        print(f"  [{status.upper():^9}] {r.get('doc_id', '?'):5} {r.get('source_file', ''):55} "
              f"chars={r.get('char_count', '-')}{flag}")

    ok = sum(1 for r in results if r.get("extract_status") == "ok")
    needs_ocr = [r for r in results if r.get("needs_ocr")]
    duplicates = find_duplicate_content(results)

    processed_manifest = {
        "snapshot": args.snapshot,
        "processed_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total": len(results),
            "extracted_ok": ok,
            "needs_ocr": len(needs_ocr),
            "duplicate_groups": len(duplicates),
        },
        "documents": results,
        "duplicate_groups": duplicates,
    }
    (out_dir / "processed_manifest.json").write_text(
        json.dumps(processed_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nExtracted {ok}/{len(results)} documents -> {out_dir}")
    if needs_ocr:
        print(f"WARNING: {len(needs_ocr)} PDF(s) look like scans (low text/page) - see needs_ocr in manifest")
    if duplicates:
        print(f"WARNING: {len(duplicates)} group(s) of documents have IDENTICAL extracted text "
              f"- check data_sources_iuh.yaml URL mapping (manual review needed)")
    return 0


def find_duplicate_content(results: list[dict]) -> list[dict]:
    """Nhóm document theo sha256 để phát hiện URL trỏ trùng nội dung
    (vd D1 và D2 vô tình cùng trỏ 1 trang do site đổi cấu trúc URL)."""
    by_hash: dict[str, list[dict]] = {}
    for r in results:
        h = r.get("sha256")
        if not h:
            continue
        by_hash.setdefault(h, []).append(r)
    return [
        {"sha256": h, "doc_ids": [r["doc_id"] for r in group], "files": [r["source_file"] for r in group]}
        for h, group in by_hash.items()
        if len(group) > 1
    ]


if __name__ == "__main__":
    sys.exit(main())
