"""Re-run quality checks for a given data_version's indexed chunk file.

Standalone from scripts/ingest_data.py (which already runs this once
inline) so quality can be re-checked/CI-gated without re-running the whole
ingest (no new embedding calls, no Qdrant/Postgres writes).

Usage:
    python scripts/check_data_quality.py --data-version data_20260711
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataops import quality_checker  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
INGEST_CONFIG = PROJECT_ROOT / "config" / "ingest.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-version", required=True)
    args = parser.parse_args()

    manifest_path = CHUNKS_DIR / f"manifest_{args.data_version}.json"
    if not manifest_path.exists():
        print(f"No manifest found for {args.data_version}: {manifest_path}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    strategy = manifest["chunking_strategy_indexed"]

    chunks_path = CHUNKS_DIR / f"{strategy}_{args.data_version}.jsonl"
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    cfg = yaml.safe_load(INGEST_CONFIG.read_text(encoding="utf-8"))
    qt = cfg["quality_thresholds"]
    report = quality_checker.check_chunks(
        chunks, min_tokens=qt["min_chunk_tokens"], max_tokens=qt["max_chunk_tokens"]
    )

    by_doc = quality_checker.summarize_by_document(chunks)
    print(f"data_version={args.data_version} strategy={strategy}")
    print(f"chunks: {len(chunks)} across {len(by_doc)} documents")
    for doc_id, count in sorted(by_doc.items()):
        print(f"  {doc_id}: {count}")
    print(f"critical_errors: {len(report.critical_errors)}")
    print(f"warnings: {len(report.warnings)}")
    if report.critical_errors:
        for err in report.critical_errors:
            print(f"  CRITICAL: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
