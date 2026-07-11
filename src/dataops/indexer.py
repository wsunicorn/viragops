"""Qdrant indexing — collection per `index_version` (config/ingest.yaml).

Naming a collection after the index_version instead of reusing one fixed
name means a re-ingest with a different embedding model or chunking config
creates a NEW collection rather than overwriting the old one, so
retrieval.yaml can pin a known-good `index_version` while a new one is
being built/evaluated (rollback = just point retrieval.yaml back).
"""

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient, models

from src.dataops.sparse_bm25 import SparseVector


def collection_name(prefix: str, index_version: str) -> str:
    return f"{prefix}_{index_version}"


def ensure_collection(
    client: QdrantClient,
    name: str,
    dense_size: int,
    dense_vector_name: str = "dense",
    sparse_vector_name: str = "sparse",
    distance: str = "cosine",
    recreate: bool = False,
) -> None:
    exists = client.collection_exists(name)
    if exists and not recreate:
        return
    if exists and recreate:
        client.delete_collection(name)

    distance_map = {
        "cosine": models.Distance.COSINE,
        "dot": models.Distance.DOT,
        "euclid": models.Distance.EUCLID,
    }
    client.create_collection(
        collection_name=name,
        vectors_config={
            dense_vector_name: models.VectorParams(size=dense_size, distance=distance_map[distance])
        },
        sparse_vectors_config={sparse_vector_name: models.SparseVectorParams()},
    )


def upsert_chunks(
    client: QdrantClient,
    name: str,
    chunks: list[dict[str, Any]],
    dense_vectors: list[list[float]],
    sparse_vectors: list[SparseVector],
    dense_vector_name: str = "dense",
    sparse_vector_name: str = "sparse",
    batch_size: int = 64,
) -> int:
    """`chunks[i]` must correspond to `dense_vectors[i]`/`sparse_vectors[i]`.
    Point id = stable hash of chunk_id (Qdrant requires int or UUID ids;
    chunk_id strings like "chunk_doc_xxx_003" are kept in the payload for
    the real identifier, matching data_schemas.md's chunk schema).
    """
    assert len(chunks) == len(dense_vectors) == len(sparse_vectors)

    points = []
    for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True):
        points.append(
            models.PointStruct(
                id=_stable_point_id(chunk["chunk_id"]),
                vector={
                    dense_vector_name: dense,
                    sparse_vector_name: models.SparseVector(
                        indices=sparse.indices, values=sparse.values
                    ),
                },
                payload=chunk,
            )
        )

    total = 0
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        client.upsert(collection_name=name, points=batch)
        total += len(batch)
    return total


def _stable_point_id(chunk_id: str) -> int:
    import hashlib

    digest = hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)  # 64-bit positive int, deterministic


def hybrid_search(
    client: QdrantClient,
    name: str,
    dense_query: list[float],
    sparse_query: SparseVector,
    top_k_dense: int = 20,
    top_k_sparse: int = 20,
    limit: int = 5,
    dense_vector_name: str = "dense",
    sparse_vector_name: str = "sparse",
) -> list[dict[str, Any]]:
    """Dense + sparse RRF fusion via Qdrant's server-side Query API
    (qdrant-client>=1.10 / qdrant server >=1.10, matches docker-compose's
    qdrant:v1.15.4) — mirrors config/retrieval.yaml's
    `retrieval.fusion.method: rrf`.
    """
    result = client.query_points(
        collection_name=name,
        prefetch=[
            models.Prefetch(query=dense_query, using=dense_vector_name, limit=top_k_dense),
            models.Prefetch(
                query=models.SparseVector(indices=sparse_query.indices, values=sparse_query.values),
                using=sparse_vector_name,
                limit=top_k_sparse,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return [{"score": p.score, **p.payload} for p in result.points]
