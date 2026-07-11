"""Self-contained BM25 sparse vector encoder using the hashing trick.

Originally planned to use fastembed's `Qdrant/bm25` (see
docs/system/modules/01_data_ragops.md decision log), but the model
download from huggingface.co's resolve endpoint was reset by the ISP mid-
transfer — the same class of CDN interference already documented for
Docker Hub in Phase 1. Rather than block Phase 3 on a flaky third-party
download, this reimplements standard BM25 (Robertson/Sparck Jones) scoring
locally:

- Terms are hashed with mmh3 into a fixed-size vocabulary
  (`config/ingest.yaml: qdrant.sparse` -> `vocab_size`, default 2**21) so
  index-time and query-time encoding never need a shared, persisted
  vocabulary file — just the corpus statistics (idf, avgdl), which are
  small enough to store directly in the ingest manifest.
- Collisions are possible but rare at this corpus size (~hundreds of
  chunks, low thousands of unique Vietnamese terms against a 2M-bucket
  space) and degrade gracefully (two colliding terms just get a merged
  document-frequency estimate) rather than failing outright.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

import mmh3

from src.dataops.vietnamese_normalizer import tokenize


@dataclass
class SparseVector:
    indices: list[int]
    values: list[float]


def _hash_term(term: str, vocab_size: int) -> int:
    return mmh3.hash(term, signed=False) % vocab_size


class BM25Sparse:
    """Fit on a chunk corpus once at ingest time, reuse at query time.

    `to_state()`/`from_state()` let the ingest manifest carry the fitted
    idf/avgdl so scripts/smoke_retrieval.py (a separate process) can
    reproduce identical query-side vectors without re-reading every chunk.
    """

    def __init__(self, vocab_size: int = 2_097_152, k1: float = 1.5, b: float = 0.75) -> None:
        self.vocab_size = vocab_size
        self.k1 = k1
        self.b = b
        self.n_docs = 0
        self.avgdl = 0.0
        self.idf: dict[int, float] = {}

    def fit(self, texts: list[str]) -> None:
        self.n_docs = len(texts)
        if not self.n_docs:
            self.avgdl = 0.0
            self.idf = {}
            return

        doc_freq: Counter[int] = Counter()
        total_len = 0
        for text in texts:
            tokens = tokenize(text)
            total_len += len(tokens)
            seen_this_doc: set[int] = set()
            for term in tokens:
                idx = _hash_term(term, self.vocab_size)
                seen_this_doc.add(idx)
            doc_freq.update(seen_this_doc)

        self.avgdl = total_len / self.n_docs if self.n_docs else 0.0
        self.idf = {
            idx: math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5)) for idx, df in doc_freq.items()
        }

    def vectorize_document(self, text: str) -> SparseVector:
        tokens = tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf: Counter[int] = Counter(_hash_term(t, self.vocab_size) for t in tokens)
        dl = len(tokens)
        norm = 1 - self.b + self.b * (dl / self.avgdl if self.avgdl else 1.0)

        indices: list[int] = []
        values: list[float] = []
        for idx, freq in tf.items():
            idf = self.idf.get(idx, 0.0)
            if idf <= 0:
                continue
            weight = idf * (freq * (self.k1 + 1)) / (freq + self.k1 * norm)
            indices.append(idx)
            values.append(weight)
        return SparseVector(indices=indices, values=values)

    def vectorize_query(self, text: str) -> SparseVector:
        """Query-side weighting: raw term frequency times idf, no length
        saturation — standard for BM25 sparse query vectors (the document
        side already carries the length-normalization term)."""
        tokens = tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf: Counter[int] = Counter(_hash_term(t, self.vocab_size) for t in tokens)
        indices: list[int] = []
        values: list[float] = []
        for idx, freq in tf.items():
            idf = self.idf.get(idx, 0.0)
            if idf <= 0:
                continue
            indices.append(idx)
            values.append(idf * freq)
        return SparseVector(indices=indices, values=values)

    def to_state(self) -> dict[str, Any]:
        return {
            "vocab_size": self.vocab_size,
            "k1": self.k1,
            "b": self.b,
            "n_docs": self.n_docs,
            "avgdl": self.avgdl,
            "idf": {str(k): v for k, v in self.idf.items()},
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> BM25Sparse:
        enc = cls(vocab_size=state["vocab_size"], k1=state["k1"], b=state["b"])
        enc.n_docs = state["n_docs"]
        enc.avgdl = state["avgdl"]
        enc.idf = {int(k): v for k, v in state["idf"].items()}
        return enc
