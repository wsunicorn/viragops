"""Semantic cache (Module 8) — Qdrant-backed, reuses the RagService's own
QdrantClient (no second connection) and the already-computed query dense
vector (no extra Gemini embedding call — quota-neutral).

Collection is named `semantic_cache_{index_version}` so a re-index
automatically invalidates old entries (same versioning convention as the
main retrieval collection, config/retrieval.yaml). Lookups additionally
filter on `prompt_version` so activating a new prompt also invalidates
stale entries — stricter than the bare data_version requirement in
module 8's acceptance criteria.
"""

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient, models


class SemanticCache:
    def __init__(
        self,
        client: QdrantClient,
        index_version: str,
        vector_size: int,
        similarity_threshold: float = 0.97,
    ) -> None:
        self._client = client
        self._collection = f"semantic_cache_{index_version}"
        self._threshold = similarity_threshold
        self._vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=self._vector_size, distance=models.Distance.COSINE),
        )

    def lookup(self, dense_q: list[float], prompt_version: str) -> dict[str, Any] | None:
        """Cosine-similarity search filtered to the current prompt_version.
        Returns the cached payload on a hit above the similarity
        threshold, else None. Never raises — a cache miss/lookup failure
        should never block answering."""
        try:
            result = self._client.query_points(
                collection_name=self._collection,
                query=dense_q,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="prompt_version", match=models.MatchValue(value=prompt_version))]
                ),
                limit=1,
                with_payload=True,
            )
        except Exception:  # noqa: BLE001 - cache là tối ưu hoá, không được chặn request
            return None
        if not result.points or result.points[0].score < self._threshold:
            return None
        return result.points[0].payload

    def store(self, dense_q: list[float], prompt_version: str, payload: dict[str, Any]) -> None:
        try:
            self._client.upsert(
                collection_name=self._collection,
                points=[
                    models.PointStruct(
                        id=abs(hash((tuple(dense_q), prompt_version))) % (2**63),
                        vector=dense_q,
                        payload={**payload, "prompt_version": prompt_version},
                    )
                ],
            )
        except Exception:  # noqa: BLE001 - ghi cache thất bại không được chặn response đã có
            pass
