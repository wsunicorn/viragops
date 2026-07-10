"""Download an immutable snapshot of IUH source documents (Phase 2).

Reads config/data_sources_iuh.yaml (D1-D12), downloads every URL into
data/raw/iuh/<snapshot>/ and writes a manifest with hashes so the snapshot
is reproducible and citable (see docs/system/experiments/data_sources_iuh.md §5).

Two passes:
  1. Top-level pages (HTML/PDF) listed in the manifest config.
  2. Depth-2: PDF/DOC/XLSX files LINKED FROM those pages (official decision
     documents like "Quyet-dinh-so-610..." usually hide behind a link on an
     HTML announcement page, not the page itself).

Re-running with --only merges into the existing manifest.json for that
snapshot instead of overwriting it, so partial runs never lose prior data.

Usage:
    python scripts/download_sources.py                 # full run, snapshot src_<today>
    python scripts/download_sources.py --snapshot src_20260710
    python scripts/download_sources.py --only D1,D5
    python scripts/download_sources.py --skip-depth2    # top-level pages only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_CONFIG = PROJECT_ROOT / "config" / "data_sources_iuh.yaml"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "iuh"

FILE_LINK_RE = re.compile(r"""href=["']([^"']+\.(?:pdf|docx?|xlsx?))["']""", re.IGNORECASE)

# Heuristic để phân biệt "văn bản quyết định/quy chế" (dùng làm nguồn RAG,
# citation) với "biểu mẫu/đơn từ" (chỉ tham khảo, không đưa vào golden set).
DECISION_HINTS = ("quyet-dinh", "qd-", "quy-che", "quy-dinh", "thong-tu", "nghi-dinh")
FORM_HINTS = ("don-", "mau-", "bieu-mau", "-don", "mau12", "mau-12")


def classify_file(filename_or_url: str) -> str:
    low = filename_or_url.lower()
    if any(h in low for h in DECISION_HINTS):
        return "decision"
    if any(h in low for h in FORM_HINTS):
        return "form"
    return "unknown"


def slugify(text: str, max_len: int = 80) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len] or "file"


def ext_for(content_type: str, url: str) -> str:
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return ".pdf"
    for known in (".docx", ".doc", ".xlsx", ".xls"):
        if url.lower().endswith(known):
            return known
    if "html" in content_type or url.endswith((".php", "/")) or "." not in url.rsplit("/", 1)[-1]:
        return ".html"
    return ".html"


def absolutize(link: str, base_url: str) -> str:
    if link.startswith("http"):
        return link
    origin = "/".join(base_url.split("/")[:3])
    return origin + link if link.startswith("/") else f"{origin}/{link}"


def download_one(
    client: httpx.Client, insecure_client: httpx.Client, url: str
) -> tuple[bytes | None, str, str, bool]:
    """Return (content, content_type, error, tls_verified).

    Một số site *.iuh.edu.vn thiếu intermediate certificate. Khi gặp lỗi SSL,
    thử lại KHÔNG verify TLS (tài liệu công khai, rủi ro thấp) nhưng đánh dấu
    tls_verified=false trong manifest để minh bạch trong báo cáo.
    """
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content, resp.headers.get("content-type", ""), "", True
    except httpx.ConnectError as exc:
        if "SSL" not in str(exc) and "certificate" not in str(exc).lower():
            return None, "", f"{type(exc).__name__}: {exc}", True
        try:
            resp = insecure_client.get(url)
            resp.raise_for_status()
            return resp.content, resp.headers.get("content-type", ""), "", False
        except httpx.HTTPError as exc2:
            return None, "", f"{type(exc2).__name__}: {exc2}", False
    except httpx.HTTPError as exc:
        return None, "", f"{type(exc).__name__}: {exc}", True


def load_existing_manifest(out_dir: Path, snapshot: str, domain: str) -> dict:
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "snapshot": snapshot,
        "domain": domain,
        "created_at": datetime.now(UTC).isoformat(),
        "documents": [],
        "discovered_file_links": [],
        "discovered_documents": [],
    }


def merge_entries(existing: list[dict], new: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
    by_key = {tuple(e.get(k) for k in key_fields): e for e in existing}
    for entry in new:
        by_key[tuple(entry.get(k) for k in key_fields)] = entry
    return list(by_key.values())


def download_top_level(
    config: dict, only_ids: set[str], client, insecure_client, out_dir: Path, delay: float
) -> tuple[list[dict], list[dict]]:
    """Pass 1: download configured pages, return (document_entries, discovered_link_dicts)."""
    entries: list[dict] = []
    discovered: list[dict] = []

    for doc in config["documents"]:
        if only_ids and doc["id"] not in only_ids:
            continue
        for i, url in enumerate(doc["urls"]):
            content, content_type, error, tls_verified = download_one(client, insecure_client, url)
            entry = {
                "doc_id": doc["id"],
                "title": doc["title"],
                "unit": doc["unit"],
                "canonical": doc.get("canonical", False) and i == 0,
                "topics": doc.get("topics", []),
                "url": url,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "tls_verified": tls_verified,
            }
            if content is None:
                entry.update(status="failed", error=error)
                print(f"  [FAIL] {doc['id']} {url}\n         {error}")
            else:
                ext = ext_for(content_type, url)
                filename = f"{doc['id'].lower()}_{i}_{slugify(doc['title'])}{ext}"
                (out_dir / filename).write_bytes(content)
                entry.update(
                    status="ok",
                    file=filename,
                    content_type=content_type,
                    size_bytes=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                )
                print(f"  [OK]   {doc['id']} {filename} ({len(content):,} bytes)")

                if ext == ".html":
                    for link in FILE_LINK_RE.findall(content.decode("utf-8", "ignore")):
                        file_url = absolutize(link, url)
                        discovered.append(
                            {
                                "doc_id": doc["id"],
                                "found_on": url,
                                "file_url": file_url,
                                "kind": classify_file(file_url),
                            }
                        )
            entries.append(entry)
            time.sleep(delay)

    return entries, discovered


def download_depth2(
    discovered_links: list[dict], client, insecure_client, out_dir: Path, delay: float
) -> list[dict]:
    """Pass 2: download every unique PDF/DOC/XLSX linked from pass-1 pages."""
    files_dir = out_dir / "files"
    files_dir.mkdir(exist_ok=True)
    entries: list[dict] = []
    seen_urls: set[str] = set()

    for link in discovered_links:
        url = link["file_url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        content, content_type, error, tls_verified = download_one(client, insecure_client, url)
        entry = {
            "doc_id": link["doc_id"],
            "found_on": link["found_on"],
            "kind": link["kind"],
            "url": url,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "tls_verified": tls_verified,
        }
        if content is None:
            entry.update(status="failed", error=error)
            print(f"  [FAIL] depth2 {link['doc_id']} {url}\n         {error}")
        else:
            ext = ext_for(content_type, url)
            original_name = url.rsplit("/", 1)[-1]
            filename = f"{link['doc_id'].lower()}_{slugify(original_name, 90)}{ext}"
            (files_dir / filename).write_bytes(content)
            entry.update(
                status="ok",
                file=f"files/{filename}",
                content_type=content_type,
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            )
            tag = "DECISION" if link["kind"] == "decision" else link["kind"].upper()
            print(f"  [OK]   depth2 [{tag}] {link['doc_id']} {filename} ({len(content):,} bytes)")
        entries.append(entry)
        time.sleep(delay)

    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=f"src_{datetime.now(UTC):%Y%m%d}")
    parser.add_argument("--only", default="", help="comma-separated doc ids, e.g. D1,D5")
    parser.add_argument("--skip-depth2", action="store_true", help="chỉ tải trang cấp 1")
    args = parser.parse_args()

    config = yaml.safe_load(MANIFEST_CONFIG.read_text(encoding="utf-8"))
    only_ids = {x.strip() for x in args.only.split(",") if x.strip()}
    delay = float(config.get("request_delay_seconds", 1.5))

    out_dir = RAW_DIR / args.snapshot
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_existing_manifest(out_dir, args.snapshot, config["domain"])

    client_opts = {
        "headers": {"User-Agent": config["user_agent"]},
        "timeout": 30.0,
        "follow_redirects": True,
    }
    with (
        httpx.Client(verify=True, **client_opts) as client,
        httpx.Client(verify=False, **client_opts) as insecure_client,
    ):
        print("== Pass 1: top-level pages ==")
        new_entries, new_discovered = download_top_level(
            config, only_ids, client, insecure_client, out_dir, delay
        )
        manifest["documents"] = merge_entries(manifest["documents"], new_entries, ("doc_id", "url"))
        manifest["discovered_file_links"] = merge_entries(
            manifest.get("discovered_file_links", []), new_discovered, ("file_url",)
        )

        if not args.skip_depth2 and manifest["discovered_file_links"]:
            print(f"\n== Pass 2: depth-2 download ({len(manifest['discovered_file_links'])} unique files) ==")
            new_depth2 = download_depth2(
                manifest["discovered_file_links"], client, insecure_client, out_dir, delay
            )
            manifest["discovered_documents"] = merge_entries(
                manifest.get("discovered_documents", []), new_depth2, ("url",)
            )

    all_docs = manifest["documents"] + manifest.get("discovered_documents", [])
    ok = sum(1 for e in all_docs if e.get("status") == "ok")
    failed = sum(1 for e in all_docs if e.get("status") == "failed")
    decisions_ok = sum(
        1 for e in manifest.get("discovered_documents", [])
        if e.get("status") == "ok" and e.get("kind") == "decision"
    )

    manifest["summary"] = {"ok": ok, "failed": failed, "decision_documents_ok": decisions_ok}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ASCII-only output: Windows console mac dinh cp1252 khong in duoc tieng Viet
    print(f"\nSnapshot {args.snapshot}: {ok} ok, {failed} failed, "
          f"{decisions_ok} decision PDFs -> {out_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
