"""Smoke-test hybrid retrieval against the indexed Qdrant collection.

Embeds the query with the same dense model used at ingest time
(RETRIEVAL_QUERY task_type, per Gemini's asymmetric embedding design) and
sparse-encodes it with the exact BM25 idf/avgdl fitted at ingest time
(data/chunks/bm25_state_<data_version>.json — see sparse_bm25.py), then
runs the same dense+sparse RRF fusion query config/retrieval.yaml
specifies.

Usage:
    python scripts/smoke_retrieval.py --query "điều kiện tốt nghiệp"
    python scripts/smoke_retrieval.py --query "..." --data-version data_20260711
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from qdrant_client import QdrantClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.dataops import embedder, indexer  # noqa: E402
from src.dataops.sparse_bm25 import BM25Sparse  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
INGEST_CONFIG = PROJECT_ROOT / "config" / "ingest.yaml"
GATEWAY_CONFIG = PROJECT_ROOT / "config" / "model_gateway.yaml"


def latest_data_version() -> str:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        raise SystemExit("No manifest_data_*.json found — run scripts/ingest_data.py first")
    return manifests[-1].stem.removeprefix("manifest_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--data-version", default=None)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    data_version = args.data_version or latest_data_version()
    manifest = json.loads((CHUNKS_DIR / f"manifest_{data_version}.json").read_text(encoding="utf-8"))
    bm25_state = json.loads((CHUNKS_DIR / f"bm25_state_{data_version}.json").read_text(encoding="utf-8"))
    bm25 = BM25Sparse.from_state(bm25_state)

    ingest_cfg = yaml.safe_load(INGEST_CONFIG.read_text(encoding="utf-8"))
    dense_cfg = ingest_cfg["embedding"]["dense"]
    qdrant_cfg = ingest_cfg["qdrant"]

    print(f"query: {args.query!r}")
    print(f"index_version={manifest['index_version']} collection={manifest['qdrant_collection']}")

    dense_vectors = embedder.embed_all(
        [args.query],
        model=manifest["embedding_model"],
        task_type=dense_cfg["task_type_query"],
        output_dimensionality=dense_cfg["output_dimensionality"],
        batch_size=1,
        batch_delay_seconds=0,
        progress_label="query-embed",
    )
    sparse_query = bm25.vectorize_query(args.query)

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)
    results = indexer.hybrid_search(
        client,
        manifest["qdrant_collection"],
        dense_query=dense_vectors[0],
        sparse_query=sparse_query,
        limit=args.limit,
        dense_vector_name=qdrant_cfg["dense_vector_name"],
        sparse_vector_name=qdrant_cfg["sparse_vector_name"],
    )

    print(f"\n{len(results)} result(s):")
    for i, r in enumerate(results, 1):
        text_preview = r["text"][:150].replace("\n", " ")
        print(f"\n[{i}] score={r['score']:.4f} document_id={r['document_id']} section={r['section']}")
        print(f"    {text_preview}...")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
