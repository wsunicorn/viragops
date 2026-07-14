"""Extractive context compression (Module 8) — no LLM call, so no
hallucination risk and no extra Gemini quota. For chunks over a char
budget, keep the sentences with the highest lexical token-overlap with
the query, in original order (preserves citation-relevant wording — a
paraphrase would break exact-quote matching the runbook and prompts rely
on)."""

from __future__ import annotations

import re
from typing import Any

from src.dataops.vietnamese_normalizer import tokenize

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\n+")


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return parts or [text]


def compress_chunk_text(text: str, query: str, max_chars: int) -> str:
    """Return `text` unchanged if it's already <= max_chars. Otherwise
    keep sentences ranked by query-token overlap (ties broken by original
    order) until the budget is used, then re-sort to original order."""
    if len(text) <= max_chars:
        return text

    query_tokens = set(tokenize(query))
    sentences = _split_sentences(text)
    scored = [
        (i, s, len(query_tokens & set(tokenize(s))))
        for i, s in enumerate(sentences)
    ]
    scored.sort(key=lambda t: t[2], reverse=True)

    kept: list[tuple[int, str]] = []
    used = 0
    for i, s, _score in scored:
        if used + len(s) > max_chars and kept:
            break
        kept.append((i, s))
        used += len(s)
    kept.sort(key=lambda t: t[0])
    return " ".join(s for _i, s in kept)


def compress_chunks(chunks: list[dict[str, Any]], query: str, max_chars: int = 800) -> list[dict[str, Any]]:
    """Apply compress_chunk_text to each chunk's `text` field, returning
    new dicts (originals untouched — callers that need pre-compression
    chunks, e.g. debug mode, keep working)."""
    compressed = []
    for c in chunks:
        new_c = dict(c)
        new_c["text"] = compress_chunk_text(c.get("text", ""), query, max_chars)
        compressed.append(new_c)
    return compressed
