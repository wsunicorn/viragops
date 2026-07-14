"""Restore a CI snapshot bundle produced by scripts/export_ci_snapshot.py
(Phase 9, Module 6 CI integration) — extracts the local chunk/manifest/
BM25-state files into data/chunks/ and recovers the Qdrant collection via
Qdrant's snapshot-upload REST API. Run this against a freshly-started,
empty Qdrant instance (docker compose up -d qdrant) before
scripts/run_evaluation.py.

Usage:
    python scripts/restore_ci_snapshot.py --snapshot-path dist/ci_snapshot_data_20260713.tar.gz
    python scripts/restore_ci_snapshot.py --snapshot-url https://github.com/.../ci_snapshot_data_20260713.tar.gz
"""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--snapshot-path", help="đường dẫn tarball local")
    src.add_argument("--snapshot-url", help="URL tải tarball về (vd GitHub Release asset)")
    args = parser.parse_args()

    settings = get_settings()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if args.snapshot_url:
            print(f"Đang tải {args.snapshot_url} ...")
            with httpx.Client(follow_redirects=True, timeout=300.0) as client:
                resp = client.get(args.snapshot_url)
                resp.raise_for_status()
            tarball_path = tmp_path / "ci_snapshot.tar.gz"
            tarball_path.write_bytes(resp.content)
        else:
            tarball_path = Path(args.snapshot_path)
            if not tarball_path.exists():
                raise SystemExit(f"Không tìm thấy {tarball_path}")

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(extract_dir, filter="data")

        meta = json.loads((extract_dir / "ci_snapshot_meta.json").read_text(encoding="utf-8"))
        print(f"Bundle: data_version={meta['data_version']} index_version={meta['index_version']} "
              f"collection={meta['collection']} (export lúc {meta.get('exported_at')})")

        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
        n_copied = 0
        for f in extract_dir.iterdir():
            if f.name in ("ci_snapshot_meta.json", "qdrant.snapshot"):
                continue
            (CHUNKS_DIR / f.name).write_bytes(f.read_bytes())
            n_copied += 1
            print(f"  restored data/chunks/{f.name}")
        print(f"Đã khôi phục {n_copied} file local vào {CHUNKS_DIR.relative_to(PROJECT_ROOT)}")

        collection = meta["collection"]
        snapshot_bytes = (extract_dir / "qdrant.snapshot").read_bytes()
        print(f"Đang upload snapshot ({len(snapshot_bytes) / 1e6:.1f} MB) vào Qdrant collection {collection!r} ...")
        with httpx.Client(base_url=settings.qdrant_url, timeout=300.0) as client:
            resp = client.post(
                f"/collections/{collection}/snapshots/upload",
                params={"priority": "snapshot"},
                files={"snapshot": ("qdrant.snapshot", snapshot_bytes, "application/octet-stream")},
            )
            resp.raise_for_status()
        print(f"Qdrant collection {collection!r} đã khôi phục xong.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
