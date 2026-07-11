"""Embed + index the remaining chunking strategies for Experiment 1 (Phase 4).

Phase 3's ingest only embedded/indexed the default strategy
(structure_aware) to save Gemini quota. The chunking-ablation experiment
needs every strategy retrievable, each in its own collection
("{prefix}_{index_version}_{strategy}") with its own BM25 state fitted on
its own corpus (idf/avgdl differ per chunk granularity).

Skips any strategy whose collection already exists with the expected
point count (idempotent — safe to rerun after a quota interruption; the
partially-indexed collection is recreated).

Usage:
    python scripts/index_all_strategies.py
    python scripts/index_all_strategies.py --only fixed,recursive
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-version", default=None)
    parser.add_argument("--only", default="", help="comma-separated strategy names")
    args = parser.parse_args()

    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        print("No ingest manifest found — run scripts/ingest_data.py first")
        return 1
    manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
    data_version = args.data_version or manifest["data_version"]
    index_version = manifest["index_version"]
    default_strategy = manifest["chunking_strategy_indexed"]
    default_collection = manifest["qdrant_collection"]

    cfg = yaml.safe_load(INGEST_CONFIG.read_text(encoding="utf-8"))
    gateway = yaml.safe_load(GATEWAY_CONFIG.read_text(encoding="utf-8"))
    dense_cfg = cfg["embedding"]["dense"]
    sparse_cfg = cfg["embedding"]["sparse"]
    qdrant_cfg = cfg["qdrant"]
    embedding_model = gateway["routes"]["embedding"]["primary"]["model"]

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    strategies = [s for s in cfg["chunking"]["strategies"] if not only or s in only]

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)

    for strategy in strategies:
        chunks_path = CHUNKS_DIR / f"{strategy}_{data_version}.jsonl"
        chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]

        # BM25 state per strategy — always (re)fit, it's cheap and local.
        bm25 = BM25Sparse(vocab_size=sparse_cfg["vocab_size"], k1=sparse_cfg["k1"], b=sparse_cfg["b"])
        bm25.fit([c["text"] for c in chunks])
        state_path = CHUNKS_DIR / f"bm25_state_{strategy}_{data_version}.json"
        state_path.write_text(json.dumps(bm25.to_state()), encoding="utf-8")

        coll = (
            default_collection
            if strategy == default_strategy
            else f"{qdrant_cfg['collection_prefix']}_{index_version}_{strategy}"
        )
        if client.collection_exists(coll):
            count = client.count(coll).count
            if count == len(chunks):
                print(f"[{strategy}] collection '{coll}' complete ({count} points) — skip")
                continue
            print(f"[{strategy}] collection '{coll}' has {count}/{len(chunks)} points — recreate")

        print(f"[{strategy}] embedding {len(chunks)} chunks -> '{coll}'")
        dense_vectors = embedder.embed_all(
            [c["text"] for c in chunks],
            model=embedding_model,
            task_type=dense_cfg["task_type_document"],
            output_dimensionality=dense_cfg["output_dimensionality"],
            batch_size=dense_cfg["batch_size"],
            batch_delay_seconds=dense_cfg["batch_delay_seconds"],
            progress_label=f"embed-{strategy}",
        )
        indexer.ensure_collection(
            client, coll,
            dense_size=dense_cfg["output_dimensionality"],
            dense_vector_name=qdrant_cfg["dense_vector_name"],
            sparse_vector_name=qdrant_cfg["sparse_vector_name"],
            distance=qdrant_cfg["distance"],
            recreate=True,
        )
        sparse_vectors = [bm25.vectorize_document(c["text"]) for c in chunks]
        n = indexer.upsert_chunks(
            client, coll, chunks, dense_vectors, sparse_vectors,
            dense_vector_name=qdrant_cfg["dense_vector_name"],
            sparse_vector_name=qdrant_cfg["sparse_vector_name"],
        )
        print(f"[{strategy}] indexed {n} points -> '{coll}'")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
