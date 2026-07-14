"""Integration test cho semantic cache (Phase 11, Module 8) — Qdrant THẬT.

Tự skip khi Qdrant chưa chạy, giống tests/integration/test_qa_flow.py.
Dùng collection riêng cho test (test_index_version_<uuid>) rồi xoá sau.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from qdrant_client import QdrantClient

from src.optimization.semantic_cache import SemanticCache

QDRANT_URL = "http://localhost:6333"


def _qdrant_ready() -> bool:
    try:
        return httpx.get(f"{QDRANT_URL}/collections", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _qdrant_ready(), reason="Qdrant not running")


@pytest.fixture
def cache():
    client = QdrantClient(url=QDRANT_URL)
    index_version = f"test_{uuid.uuid4().hex[:8]}"
    sc = SemanticCache(client, index_version=index_version, vector_size=8, similarity_threshold=0.97)
    yield sc
    client.delete_collection(f"semantic_cache_{index_version}")


def _vec(seed: float, size: int = 8) -> list[float]:
    return [seed] * size


def test_miss_on_empty_cache(cache):
    assert cache.lookup(_vec(0.5), prompt_version="p7") is None


def test_hit_after_store(cache):
    cache.store(_vec(0.5), prompt_version="p7", payload={"answer": "42", "citations": [], "refusal": False})
    hit = cache.lookup(_vec(0.5), prompt_version="p7")
    assert hit is not None
    assert hit["answer"] == "42"


def test_miss_on_different_prompt_version(cache):
    cache.store(_vec(0.5), prompt_version="p7", payload={"answer": "42", "citations": [], "refusal": False})
    assert cache.lookup(_vec(0.5), prompt_version="p8") is None


def test_miss_on_dissimilar_vector(cache):
    cache.store(_vec(0.9, size=8), prompt_version="p7", payload={"answer": "x", "citations": [], "refusal": False})
    # Vector trực giao (mọi chiều = 0 trừ 1 chiều khác) -> cosine similarity thấp
    dissimilar = [0.0] * 7 + [1.0]
    assert cache.lookup(dissimilar, prompt_version="p7") is None


def test_lookup_never_raises_on_bad_vector_size(cache):
    # vector sai chiều -> Qdrant lỗi -> lookup phải nuốt lỗi, trả None
    assert cache.lookup([0.1, 0.2], prompt_version="p7") is None
