"""Unified retrieval interface for Phase 4 experiments (Module 2).

`retrieve()` executes one retrieval config against one Qdrant collection.
Query vectors are passed in pre-computed: dense query embedding costs
Gemini quota, so the experiment runner embeds each golden-set question
ONCE and reuses the cached vector across every config/collection
(scripts/run_experiment.py) instead of re-embedding per config.

Modes (config/retrieval.yaml's retrieval.type, plus fusion variants):
- dense        — cosine ANN over the named dense vector
- sparse       — BM25 sparse vector search (self-written encoder,
                 src/dataops/sparse_bm25.py)
- hybrid_rrf   — server-side Reciprocal Rank Fusion of both prefetches
- hybrid_dbsf  — server-side Distribution-Based Score Fusion (needs
                 qdrant >= 1.11; docker-compose pins v1.15.4, client
                 enum verified to expose Fusion.DBSF)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from src.dataops.sparse_bm25 import SparseVector

MODES = ("dense", "sparse", "hybrid_rrf", "hybrid_dbsf")


@dataclass
class RetrievalConfig:
    config_id: str
    mode: str  # one of MODES
    top_k_before: int = 20  # per-branch candidate depth (prefetch limit)
    limit: int = 5  # final results returned
    rerank: str = "none"  # none | gemini_listwise
    dense_vector_name: str = "dense"
    sparse_vector_name: str = "sparse"

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unknown retrieval mode: {self.mode}")


def retrieve(
    client: QdrantClient,
    collection: str,
    config: RetrievalConfig,
    dense_query: list[float] | None,
    sparse_query: SparseVector | None,
    fetch_limit: int | None = None,
) -> list[dict[str, Any]]:
    """Run one query. `fetch_limit` overrides config.limit (rerankers need
    a deeper candidate list than the final cut)."""
    limit = fetch_limit or config.limit

    if config.mode == "dense":
        if dense_query is None:
            raise ValueError("dense mode requires a dense query vector")
        result = client.query_points(
            collection_name=collection,
            query=dense_query,
            using=config.dense_vector_name,
            limit=limit,
            with_payload=True,
        )
    elif config.mode == "sparse":
        if sparse_query is None:
            raise ValueError("sparse mode requires a sparse query vector")
        result = client.query_points(
            collection_name=collection,
            query=models.SparseVector(indices=sparse_query.indices, values=sparse_query.values),
            using=config.sparse_vector_name,
            limit=limit,
            with_payload=True,
        )
    else:  # hybrid_rrf | hybrid_dbsf
        if dense_query is None or sparse_query is None:
            raise ValueError("hybrid modes require both query vectors")
        fusion = models.Fusion.RRF if config.mode == "hybrid_rrf" else models.Fusion.DBSF
        result = client.query_points(
            collection_name=collection,
            prefetch=[
                models.Prefetch(
                    query=dense_query,
                    using=config.dense_vector_name,
                    limit=config.top_k_before,
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_query.indices, values=sparse_query.values
                    ),
                    using=config.sparse_vector_name,
                    limit=config.top_k_before,
                ),
            ],
            query=models.FusionQuery(fusion=fusion),
            limit=limit,
            with_payload=True,
        )

    return [{"score": p.score, **p.payload} for p in result.points]
