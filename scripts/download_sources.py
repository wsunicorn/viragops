"""Download an immutable snapshot of IUH source documents (Phase 2).

Reads config/data_sources_iuh.yaml (D1-D12), downloads every URL into
data/raw/iuh/<snapshot>/ and writes a manifest with hashes so the snapshot
is reproducible and citable (see docs/system/experiments/data_sources_iuh.md §5).

Also scans downloaded HTML for linked PDF/DOC files and reports them for
manual follow-up (official decision documents usually hide behind links).

Usage:
    python scripts/download_sources.py                 # snapshot src_<today>
    python scripts/download_sources.py --snapshot src_20260710
    python scripts/download_sources.py --only D1,D5
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


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len] or "page"


def ext_for(content_type: str, url: str) -> str:
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return ".pdf"
    if "html" in content_type or url.endswith((".php", "/")):
        return ".html"
    for known in (".docx", ".doc", ".xlsx", ".xls"):
        if url.lower().endswith(known):
            return known
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=f"src_{datetime.now(UTC):%Y%m%d}")
    parser.add_argument("--only", default="", help="comma-separated doc ids, e.g. D1,D5")
    args = parser.parse_args()

    config = yaml.safe_load(MANIFEST_CONFIG.read_text(encoding="utf-8"))
    only_ids = {x.strip() for x in args.only.split(",") if x.strip()}
    delay = float(config.get("request_delay_seconds", 1.5))

    out_dir = RAW_DIR / args.snapshot
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "snapshot": args.snapshot,
        "domain": config["domain"],
        "created_at": datetime.now(UTC).isoformat(),
        "documents": [],
    }
    discovered_files: list[dict] = []
    ok = failed = 0

    client_opts = {
        "headers": {"User-Agent": config["user_agent"]},
        "timeout": 30.0,
        "follow_redirects": True,
    }
    with (
        httpx.Client(verify=True, **client_opts) as client,
        httpx.Client(verify=False, **client_opts) as insecure_client,
    ):
        for doc in config["documents"]:
            if only_ids and doc["id"] not in only_ids:
                continue
            for i, url in enumerate(doc["urls"]):
                content, content_type, error, tls_verified = download_one(
                    client, insecure_client, url
                )
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
                    failed += 1
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
                    ok += 1
                    print(f"  [OK]   {doc['id']} {filename} ({len(content):,} bytes)")

                    if ext == ".html":
                        for link in FILE_LINK_RE.findall(content.decode("utf-8", "ignore")):
                            discovered_files.append(
                                {"doc_id": doc["id"], "found_on": url,
                                 "file_url": absolutize(link, url)}
                            )
                manifest["documents"].append(entry)
                time.sleep(delay)

    manifest["summary"] = {"ok": ok, "failed": failed}
    manifest["discovered_file_links"] = discovered_files
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ASCII-only output: Windows console mặc định cp1252 không in được tiếng Việt
    print(f"\nSnapshot {args.snapshot}: {ok} ok, {failed} failed -> {out_dir}")
    if discovered_files:
        print(f"Found {len(discovered_files)} attached file links (PDF/DOC) - see manifest.json")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
