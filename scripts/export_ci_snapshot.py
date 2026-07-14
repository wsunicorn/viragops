"""Export a CI-ready snapshot bundle (Phase 9, Module 6 CI integration).

Packages everything scripts/run_evaluation.py + RagService need at runtime
that ISN'T committed to git (data/chunks/* is gitignored — see
.gitignore) into one tarball: the Qdrant collection (via Qdrant's own
snapshot REST API) + the local chunk JSONL/manifest/BM25-state files
data_version's ingest produced. A GitHub Actions runner has none of this
by default; re-running the full ingest pipeline in CI would cost real
Gemini embedding quota on every run (this project has repeatedly hit
free-tier exhaustion just from manual runs — see CHECKLIST Phase 8
"Chưa tốt"), so this is built ONCE locally and uploaded as a GitHub
Release asset; CI only downloads + restores it (scripts/restore_ci_snapshot.py).

Run this again and re-upload whenever data_version/index_version changes
(new ingest). Uses Qdrant's plain REST API directly (POST .../snapshots,
GET .../snapshots/{name}) rather than the Python client's snapshot
wrappers — the REST contract is simpler to reason about for a one-shot
export/import script than chasing the client library's internal typing.

Usage:
    python scripts/export_ci_snapshot.py
    python scripts/export_ci_snapshot.py --out dist/ci_snapshot.tar.gz
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tarfile
import time
from pathlib import Path

import httpx
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
RETRIEVAL_CONFIG_PATH = PROJECT_ROOT / "config" / "retrieval.yaml"
INGEST_CONFIG_PATH = PROJECT_ROOT / "config" / "ingest.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None, help="đường dẫn tarball output (mặc định dist/ci_snapshot_<data_version>.tar.gz)")
    args = parser.parse_args()

    settings = get_settings()
    rcfg = yaml.safe_load(RETRIEVAL_CONFIG_PATH.read_text(encoding="utf-8"))
    icfg = yaml.safe_load(INGEST_CONFIG_PATH.read_text(encoding="utf-8"))
    data_version = rcfg["data_version"]
    index_version = rcfg["index_version"]
    collection = f"{icfg['qdrant']['collection_prefix']}_{index_version}"

    # data_version đã có dạng "data_20260713" -> tên file thật là
    # "manifest_data_20260713.json" (xem scripts/ingest_data.py).
    manifest_path = CHUNKS_DIR / f"manifest_{data_version}.json"
    if not manifest_path.exists():
        raise SystemExit(f"Không tìm thấy manifest cho {data_version} trong {CHUNKS_DIR}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    strategy = manifest["chunking_strategy_indexed"]

    chunks_jsonl = CHUNKS_DIR / f"{strategy}_{data_version}.jsonl"
    bm25_state = CHUNKS_DIR / f"bm25_state_{strategy}_{data_version}.json"
    if not bm25_state.exists():
        bm25_state = CHUNKS_DIR / f"bm25_state_{data_version}.json"
    for p in (chunks_jsonl, bm25_state):
        if not p.exists():
            raise SystemExit(f"Thiếu file cần thiết: {p}")

    staging = PROJECT_ROOT / "dist" / "_ci_snapshot_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    shutil.copy(manifest_path, staging / manifest_path.name)
    shutil.copy(chunks_jsonl, staging / chunks_jsonl.name)
    shutil.copy(bm25_state, staging / bm25_state.name)
    (staging / "ci_snapshot_meta.json").write_text(
        json.dumps(
            {
                "data_version": data_version,
                "index_version": index_version,
                "collection": collection,
                "chunking_strategy": strategy,
                "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Tạo Qdrant snapshot cho collection {collection!r} ...")
    with httpx.Client(base_url=settings.qdrant_url, timeout=120.0) as client:
        resp = client.post(f"/collections/{collection}/snapshots", params={"wait": "true"})
        resp.raise_for_status()
        snapshot_name = resp.json()["result"]["name"]
        print(f"  snapshot: {snapshot_name}")

        print("  đang tải snapshot về ...")
        dl = client.get(f"/collections/{collection}/snapshots/{snapshot_name}")
        dl.raise_for_status()
        snapshot_path = staging / "qdrant.snapshot"
        snapshot_path.write_bytes(dl.content)
        print(f"  -> {snapshot_path} ({len(dl.content) / 1e6:.1f} MB)")

    out_path = Path(args.out) if args.out else PROJECT_ROOT / "dist" / f"ci_snapshot_{data_version}.tar.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out_path, "w:gz") as tar:
        for f in staging.iterdir():
            tar.add(f, arcname=f.name)
    shutil.rmtree(staging)

    print(f"\nBundle -> {out_path.relative_to(PROJECT_ROOT)} ({out_path.stat().st_size / 1e6:.1f} MB)")
    print(
        "\nBước tiếp theo (làm 1 lần, làm lại mỗi khi data_version/index_version đổi):\n"
        "  1. Vào GitHub repo -> Releases -> Draft a new release (hoặc dùng release có sẵn, vd tag `ci-data`).\n"
        f"  2. Upload {out_path.name} làm 1 asset của release đó.\n"
        "  3. Copy URL download trực tiếp của asset (chuột phải -> Copy link), lưu vào biến\n"
        "     repo (Settings -> Secrets and variables -> Actions -> Variables) tên CI_SNAPSHOT_URL.\n"
        "  4. Xem docs/system/CHECKLIST_IMPLEMENTATION.md Phase 9 để biết cách wire vào workflow."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
