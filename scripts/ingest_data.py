"""Phase 3 (Module 1 DataOps/RAGOps) ingest pipeline orchestrator.

Load documents (src/dataops/metadata_extractor.py) -> normalize
(vietnamese_normalizer) -> chunk with all 4 strategies (chunker.py, chunk
files written for all 4 so they exist for Phase 4 retrieval comparisons)
-> quality check (quality_checker.py) -> embed dense (Gemini,
embedder.py) + sparse (BM25, sparse_bm25.py) for the *default* strategy
only -> index into Qdrant -> mirror document/chunk metadata into Postgres
-> write a data_version/index_version manifest.

Only `chunking.default_strategy` (config/ingest.yaml, currently
structure_aware) gets embedded + indexed — embedding all 4 strategies'
worth of chunks would multiply Gemini quota usage for chunk sets that
exist purely for offline comparison, not for serving retrieval.

Usage:
    python scripts/ingest_data.py --config config/ingest.yaml
    python scripts/ingest_data.py --config config/ingest.yaml --skip-embed --skip-qdrant --skip-postgres
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from qdrant_client import QdrantClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.dataops import embedder, indexer, quality_checker, version_manager  # noqa: E402
from src.dataops.chunker import CHUNKERS, RawChunk, count_tokens  # noqa: E402
from src.dataops.metadata_extractor import load_documents  # noqa: E402
from src.dataops.sparse_bm25 import BM25Sparse  # noqa: E402
from src.dataops.vietnamese_normalizer import (  # noqa: E402
    clean_text_keep_pages,
    extract_page_range,
    normalize_for_search,
    strip_page_sentinels,
)

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
GATEWAY_CONFIG = PROJECT_ROOT / "config" / "model_gateway.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_chunks_for_strategy(
    documents: list, strategy: str, strategy_cfg: dict[str, Any], data_version: str
) -> list[dict[str, Any]]:
    chunk_fn = CHUNKERS[strategy]
    # ingest.yaml carries documentation-only params per strategy (e.g.
    # structure_aware's `unit: dieu`) that the chunker function itself
    # doesn't take as a kwarg (the Điều/Khoản split is hard-coded logic,
    # not configurable) — only pass through what the function accepts.
    accepted = set(inspect.signature(chunk_fn).parameters)
    kwargs = {k: v for k, v in strategy_cfg.items() if k in accepted}

    out: list[dict[str, Any]] = []
    for doc in documents:
        raw_chunks: list[RawChunk] = chunk_fn(doc.text, **kwargs)
        local_id_by_index = {
            rc.chunk_index: f"chunk_{doc.document_id}_{strategy}_{rc.chunk_index:04d}"
            for rc in raw_chunks
        }
        # Carry-forward page tracking: chunk_index follows document reading
        # order for all 4 strategies, so a chunk with no [PG:N] sentinel of
        # its own is on whatever page the last-seen sentinel said — it must
        # be, since no page boundary occurred between them. Genuinely
        # page-less documents (HTML-sourced, never had OCR markers) keep
        # page_start/page_end = None honestly instead of a guessed value.
        last_page: int | None = None
        for rc in sorted(raw_chunks, key=lambda r: r.chunk_index):
            chunk_start_page = last_page
            page_min, page_max = extract_page_range(rc.text)
            if page_min is not None:
                page_start = chunk_start_page if chunk_start_page is not None else page_min
                page_end = page_max
                last_page = page_max
            else:
                page_start = page_end = chunk_start_page

            chunk_id = local_id_by_index[rc.chunk_index]
            parent_chunk_id = (
                local_id_by_index.get(rc.parent_index) if rc.parent_index is not None else None
            )
            clean_chunk_text = strip_page_sentinels(rc.text).strip()
            out.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": doc.document_id,
                    "data_version": data_version,
                    "chunk_index": rc.chunk_index,
                    "text": clean_chunk_text,
                    "normalized_text": normalize_for_search(clean_chunk_text),
                    "token_count": count_tokens(clean_chunk_text),
                    "page_start": page_start,
                    "page_end": page_end,
                    "section": rc.section,
                    "chunking_strategy": rc.chunking_strategy,
                    "parent_chunk_id": parent_chunk_id,
                    "metadata": {
                        "heading": rc.heading,
                        "effective_date": doc.effective_date,
                        "document_title": doc.title,
                        **rc.metadata,
                    },
                }
            )
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_documents_postgres(conn, documents: list) -> None:
    import psycopg.types.json as pg_json

    with conn.cursor() as cur:
        for doc in documents:
            cur.execute(
                """
                INSERT INTO documents
                    (document_id, domain, title, source_uri, source_type,
                     source_version, effective_date, ingested_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    title = EXCLUDED.title, source_uri = EXCLUDED.source_uri,
                    source_type = EXCLUDED.source_type, source_version = EXCLUDED.source_version,
                    effective_date = EXCLUDED.effective_date, ingested_at = EXCLUDED.ingested_at,
                    metadata = EXCLUDED.metadata
                """,
                (
                    doc.document_id, doc.domain, doc.title, doc.source_uri, doc.source_type,
                    doc.source_version, doc.effective_date, doc.ingested_at,
                    pg_json.Jsonb(doc.metadata),
                ),
            )
    conn.commit()


def write_chunks_postgres(conn, chunks: list[dict[str, Any]]) -> None:
    import psycopg.types.json as pg_json

    with conn.cursor() as cur:
        # parents first (self-referencing FK)
        ordered = sorted(chunks, key=lambda c: c["parent_chunk_id"] is not None)
        for c in ordered:
            cur.execute(
                """
                INSERT INTO chunks
                    (chunk_id, document_id, data_version, chunk_index, text, normalized_text,
                     token_count, page_start, page_end, section, chunking_strategy,
                     parent_chunk_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    text = EXCLUDED.text, normalized_text = EXCLUDED.normalized_text,
                    token_count = EXCLUDED.token_count, section = EXCLUDED.section,
                    metadata = EXCLUDED.metadata
                """,
                (
                    c["chunk_id"], c["document_id"], c["data_version"], c["chunk_index"], c["text"],
                    c["normalized_text"], c["token_count"], c["page_start"], c["page_end"],
                    c["section"], c["chunking_strategy"], c["parent_chunk_id"],
                    pg_json.Jsonb(c["metadata"]),
                ),
            )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "ingest.yaml")
    parser.add_argument("--skip-embed", action="store_true", help="chunk+quality-check only, no Gemini calls")
    parser.add_argument("--skip-qdrant", action="store_true")
    parser.add_argument("--skip-postgres", action="store_true")
    parser.add_argument("--recreate-collection", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    gateway_cfg = load_yaml(GATEWAY_CONFIG)

    processed_dir = PROJECT_ROOT / cfg["source"]["processed_dir"]
    documents = load_documents(processed_dir, source_version=cfg["source"]["snapshot"])
    print(f"Loaded {len(documents)} documents from {cfg['source']['snapshot']}")

    for doc in documents:
        # Keep [PG:N] page sentinels through chunking (build_chunks_for_
        # strategy reads + strips them per-chunk) instead of deleting page
        # markers upfront — that used to be the reason page_start/page_end
        # were always None (see CHECKLIST Phase 3 "Chưa tốt").
        doc.text = clean_text_keep_pages(doc.text)

    data_version = version_manager.make_data_version()
    default_strategy = cfg["chunking"]["default_strategy"]

    chunks_by_strategy: dict[str, list[dict[str, Any]]] = {}
    for strategy, strategy_cfg in cfg["chunking"]["strategies"].items():
        chunks = build_chunks_for_strategy(documents, strategy, strategy_cfg, data_version)
        chunks_by_strategy[strategy] = chunks
        out_path = CHUNKS_DIR / f"{strategy}_{data_version}.jsonl"
        write_jsonl(out_path, chunks)
        print(f"  [{strategy}] {len(chunks)} chunks -> {out_path.relative_to(PROJECT_ROOT)}")

    indexed_chunks = chunks_by_strategy[default_strategy]

    qt = cfg["quality_thresholds"]
    report = quality_checker.check_chunks(
        indexed_chunks, min_tokens=qt["min_chunk_tokens"], max_tokens=qt["max_chunk_tokens"]
    )
    report_path = CHUNKS_DIR / f"quality_report_{data_version}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Quality report: {len(report.critical_errors)} critical, {len(report.warnings)} warnings "
          f"-> {report_path.relative_to(PROJECT_ROOT)}")
    if not report.is_critical_clean:
        print("REFUSED: critical data quality errors present, aborting before embed/index.")
        for err in report.critical_errors:
            print(f"  - {err}")
        return 1

    dense_cfg = cfg["embedding"]["dense"]
    embed_route = gateway_cfg["routes"]["embedding"]["primary"]
    embedding_model = embed_route["model"]
    index_version = version_manager.make_index_version(data_version, embedding_model)
    qdrant_cfg = cfg["qdrant"]
    coll_name = indexer.collection_name(qdrant_cfg["collection_prefix"], index_version)

    sparse_cfg = cfg["embedding"]["sparse"]
    bm25 = BM25Sparse(
        vocab_size=sparse_cfg["vocab_size"], k1=sparse_cfg["k1"], b=sparse_cfg["b"]
    )
    bm25.fit([c["text"] for c in indexed_chunks])
    bm25_state_path = CHUNKS_DIR / f"bm25_state_{data_version}.json"
    bm25_state_path.write_text(json.dumps(bm25.to_state()), encoding="utf-8")
    print(f"BM25 fitted on {len(indexed_chunks)} chunks -> {bm25_state_path.relative_to(PROJECT_ROOT)}")

    dense_vectors: list[list[float]] = []
    if not args.skip_embed:
        dense_vectors = embedder.embed_all(
            [c["text"] for c in indexed_chunks],
            model=embedding_model,
            task_type=dense_cfg["task_type_document"],
            output_dimensionality=dense_cfg["output_dimensionality"],
            batch_size=dense_cfg["batch_size"],
            batch_delay_seconds=dense_cfg["batch_delay_seconds"],
            progress_label="dense-embed",
        )
        print(f"Embedded {len(dense_vectors)} dense vectors ({dense_cfg['output_dimensionality']}d)")
    else:
        print("--skip-embed: no Gemini calls made, no Qdrant indexing possible")

    if not args.skip_qdrant and dense_vectors:
        settings = get_settings()
        client = QdrantClient(url=settings.qdrant_url)
        indexer.ensure_collection(
            client, coll_name,
            dense_size=dense_cfg["output_dimensionality"],
            dense_vector_name=qdrant_cfg["dense_vector_name"],
            sparse_vector_name=qdrant_cfg["sparse_vector_name"],
            distance=qdrant_cfg["distance"],
            recreate=args.recreate_collection,
        )
        sparse_vectors = [bm25.vectorize_document(c["text"]) for c in indexed_chunks]
        n = indexer.upsert_chunks(
            client, coll_name, indexed_chunks, dense_vectors, sparse_vectors,
            dense_vector_name=qdrant_cfg["dense_vector_name"],
            sparse_vector_name=qdrant_cfg["sparse_vector_name"],
        )
        print(f"Indexed {n} points -> Qdrant collection '{coll_name}'")

    if not args.skip_postgres:
        import psycopg

        settings = get_settings()
        try:
            with psycopg.connect(settings.postgres_dsn) as conn:
                write_documents_postgres(conn, documents)
                write_chunks_postgres(conn, indexed_chunks)
            print(f"Wrote {len(documents)} documents + {len(indexed_chunks)} chunks -> Postgres")
        except psycopg.OperationalError as exc:
            print(f"WARNING: could not write to Postgres ({exc}) — Qdrant index is still valid, "
                  f"but metadata registry is out of sync. Run scripts/init_postgres_schema.py first "
                  f"and rerun.")

    manifest = version_manager.new_manifest(
        data_version=data_version,
        index_version=index_version,
        ingest_config_id=cfg["ingest_config_id"],
        source_snapshot=cfg["source"]["snapshot"],
        chunking_strategy_indexed=default_strategy,
        embedding_model=embedding_model,
        embedding_output_dimensionality=dense_cfg["output_dimensionality"],
        sparse_provider=sparse_cfg["provider"],
        qdrant_collection=coll_name,
        document_count=len(documents),
        chunk_count=len(indexed_chunks),
        chunk_counts_by_strategy={k: len(v) for k, v in chunks_by_strategy.items()},
        quality_report=report.to_dict(),
    )
    manifest_path = CHUNKS_DIR / f"manifest_{data_version}.json"
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nManifest -> {manifest_path.relative_to(PROJECT_ROOT)}")
    print(f"data_version={data_version} index_version={index_version}")
    print("Update config/retrieval.yaml data_version/index_version to these values when ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
