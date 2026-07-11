"""4 chunking strategies for Phase 3 (Module 1 DataOps/RAGOps).

Vietnamese IUH regulation text (decisions/quy chế) mostly follows a
`Chương > Điều > Khoản > Điểm` legal structure (see
docs/system/modules/01_data_ragops.md), but a meaningful share of the
corpus is scraped from camnang.iuh.edu.vn-style pages that use plain
numbered lists without "Điều N." headings at all (confirmed by reading
data/processed/iuh/src_20260710/d5_..., d13_... — see golden_set_review.md
for the source survey). `chunk_structure_aware` therefore falls back to
paragraph-window chunking for documents with no detectable Điều headings,
so every document contributes at least some retrievable chunks instead of
silently disappearing from the index.

Each `chunk_*` function returns a flat list of `RawChunk` — document-level
identity (`document_id`, `data_version`, `chunk_id`) is assigned by the
caller (scripts/ingest_data.py), not here, so this module stays a pure,
independently testable function library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

import tiktoken

from src.dataops.vietnamese_normalizer import normalize_for_search

_CHUONG_RE = re.compile(r"^Chương\s+([IVXLCDM]+)\s*$", re.MULTILINE)
_DIEU_RE = re.compile(r"^Điều\s+(\d+)\.\s*(.*)$", re.MULTILINE)
_KHOAN_RE = re.compile(r"^(\d{1,2})\.\s+", re.MULTILINE)
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


@lru_cache(maxsize=1)
def _encoder() -> tiktoken.Encoding:
    # cl100k_base is an approximation, not Gemini's real tokenizer — good
    # enough for chunk-sizing decisions, not for exact cost accounting.
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    if not text.strip():
        return 0
    return len(_encoder().encode(text))


@dataclass
class RawChunk:
    chunk_index: int
    text: str
    chunking_strategy: str
    section: str | None = None
    heading: str | None = None
    parent_index: int | None = None  # index into the same result list, resolved to chunk_id by caller
    token_count: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.token_count:
            self.token_count = count_tokens(self.text)


def _finalize(chunks: list[RawChunk]) -> list[RawChunk]:
    for chunk in chunks:
        if not chunk.token_count:
            chunk.token_count = count_tokens(chunk.text)
    return chunks


# --- Strategy 1: fixed-size sliding window (token-count based) ---------


def chunk_fixed(text: str, chunk_size_tokens: int = 300, overlap_tokens: int = 50) -> list[RawChunk]:
    """Slide a fixed token window over the whole text, ignoring structure.

    Simple baseline for Phase 4 retrieval comparisons — not the strategy
    indexed by default (see config/ingest.yaml `default_strategy`).
    """
    text = text.strip()
    if not text:
        return []

    enc = _encoder()
    tokens = enc.encode(text)
    step = max(chunk_size_tokens - overlap_tokens, 1)

    chunks: list[RawChunk] = []
    idx = 0
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_size_tokens]
        if not window:
            break
        chunk_text = enc.decode(window)
        chunks.append(RawChunk(chunk_index=idx, text=chunk_text, chunking_strategy="fixed"))
        idx += 1
        if start + chunk_size_tokens >= len(tokens):
            break
    return _finalize(chunks)


# --- Strategy 2: recursive separator-based splitting --------------------


def _split_recursive(text: str, separators: list[str], chunk_size_tokens: int) -> list[str]:
    if count_tokens(text) <= chunk_size_tokens or not separators:
        return [text] if text.strip() else []

    sep, *rest = separators
    parts = [p for p in text.split(sep) if p.strip()]
    if len(parts) <= 1:
        return _split_recursive(text, rest, chunk_size_tokens)

    out: list[str] = []
    for part in parts:
        out.extend(_split_recursive(part, rest, chunk_size_tokens))
    return out


def chunk_recursive(
    text: str,
    chunk_size_tokens: int = 400,
    overlap_tokens: int = 60,
    separators: list[str] | None = None,
) -> list[RawChunk]:
    """Recursively split on decreasing-granularity separators, then merge
    small pieces back up to ~chunk_size_tokens with a token overlap between
    consecutive merged chunks (classic LangChain-style recursive splitter,
    reimplemented locally to avoid adding the dependency for 4 functions).
    """
    text = text.strip()
    if not text:
        return []
    separators = separators or ["\n\n", "\n", ". ", " "]

    pieces = _split_recursive(text, separators, chunk_size_tokens)
    if not pieces:
        return []

    merged: list[str] = []
    buf = ""
    for piece in pieces:
        candidate = f"{buf} {piece}".strip() if buf else piece
        if count_tokens(candidate) <= chunk_size_tokens or not buf:
            buf = candidate
        else:
            merged.append(buf)
            enc = _encoder()
            overlap_ids = enc.encode(buf)[-overlap_tokens:] if overlap_tokens else []
            buf = (enc.decode(overlap_ids) + " " + piece).strip() if overlap_ids else piece
    if buf.strip():
        merged.append(buf)

    chunks = [
        RawChunk(chunk_index=i, text=m, chunking_strategy="recursive") for i, m in enumerate(merged)
    ]
    return _finalize(chunks)


# --- Structure parsing shared by structure_aware and parent_child -------


def _chuong_context(text: str, pos: int) -> str | None:
    """Nearest 'Chương <N>' + title line at/before byte offset `pos`."""
    last: str | None = None
    for m in _CHUONG_RE.finditer(text):
        if m.start() > pos:
            break
        title_line = ""
        rest = text[m.end() :].lstrip("\n")
        first_line = rest.split("\n", 1)[0].strip()
        if first_line and not first_line.startswith(("Điều", "Chương")):
            title_line = first_line
        last = f"Chương {m.group(1)}" + (f" — {title_line}" if title_line else "")
    return last


def _split_by_dieu(text: str) -> list[tuple[str, str | None, str]] | None:
    """Split on 'Điều N. ...' headings. Returns None if the document has no
    such heading at all (camnang.iuh.edu.vn-style pages — see module
    docstring), so the caller can fall back to paragraph chunking.
    """
    matches = list(_DIEU_RE.finditer(text))
    if not matches:
        return None

    sections: list[tuple[str, str | None, str]] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.start() : end].strip()
        if not body:
            continue
        section_label = f"Điều {m.group(1)}"
        dieu_title = m.group(2).strip()
        heading = _chuong_context(text, m.start())
        heading = f"{heading} — {dieu_title}" if heading and dieu_title else (heading or dieu_title or None)
        sections.append((section_label, heading, body))
    return sections


def _split_khoan(dieu_body: str) -> list[tuple[str, str]]:
    """Split one Điều's body into (khoan_label, clause_text) pairs.

    The Điều's own opening line ("Điều N. Title") is kept attached to
    Khoản 1 rather than dropped, so no text is lost if a caller only keeps
    per-Khoản chunks (parent_child strategy).
    """
    matches = list(_KHOAN_RE.finditer(dieu_body, dieu_body.find("\n") + 1 if "\n" in dieu_body else 0))
    if not matches:
        return [("", dieu_body)]

    out: list[tuple[str, str]] = []
    header = dieu_body[: matches[0].start()].strip()
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(dieu_body)
        clause = dieu_body[m.start() : end].strip()
        text_ = f"{header}\n{clause}".strip() if i == 0 and header else clause
        out.append((m.group(1), text_))
    return out


# --- Strategy 3: structure-aware (Điều-based, paragraph fallback) -------


def chunk_structure_aware(text: str, max_tokens: int = 600) -> list[RawChunk]:
    """Default strategy indexed into Qdrant (config/ingest.yaml).

    One chunk per Điều (keeps every Khoản/Điểm inside it together, so a
    citation like "Điều 6, Khoản 4" always resolves to a chunk that
    actually contains Khoản 4). An Điều longer than `max_tokens` is split
    at Khoản boundaries into consecutive groups that fit the budget,
    labelled "Điều N, Khoản a-b". Documents with no Điều heading at all
    fall back to plain paragraph-window chunking (section=None).
    """
    text = text.strip()
    if not text:
        return []

    sections = _split_by_dieu(text)
    if sections is None:
        return _chunk_paragraphs(text, max_tokens, strategy="structure_aware")

    chunks: list[RawChunk] = []
    idx = 0
    for section_label, heading, body in sections:
        if count_tokens(body) <= max_tokens:
            chunks.append(
                RawChunk(
                    chunk_index=idx,
                    text=body,
                    chunking_strategy="structure_aware",
                    section=section_label,
                    heading=heading,
                )
            )
            idx += 1
            continue

        # Điều too long: group consecutive Khoản until the budget is hit.
        khoan_pairs = _split_khoan(body)
        group: list[str] = []
        group_labels: list[str] = []
        for label, clause_text in khoan_pairs:
            candidate = "\n".join([*group, clause_text])
            if group and count_tokens(candidate) > max_tokens:
                span = f"{group_labels[0]}-{group_labels[-1]}" if len(group_labels) > 1 else group_labels[0]
                chunks.append(
                    RawChunk(
                        chunk_index=idx,
                        text="\n".join(group),
                        chunking_strategy="structure_aware",
                        section=f"{section_label}, Khoản {span}" if span else section_label,
                        heading=heading,
                    )
                )
                idx += 1
                group, group_labels = [clause_text], [label]
            else:
                group.append(clause_text)
                group_labels.append(label)
        if group:
            span = f"{group_labels[0]}-{group_labels[-1]}" if len(group_labels) > 1 else group_labels[0]
            chunks.append(
                RawChunk(
                    chunk_index=idx,
                    text="\n".join(group),
                    chunking_strategy="structure_aware",
                    section=f"{section_label}, Khoản {span}" if span else section_label,
                    heading=heading,
                )
            )
            idx += 1
    return _finalize(chunks)


def _chunk_paragraphs(text: str, max_tokens: int, strategy: str) -> list[RawChunk]:
    """Paragraph-window fallback for documents without legal-style headings.

    Splits on blank lines first (semantic paragraph boundaries); any
    paragraph still over budget — common in scraped camnang.iuh.edu.vn
    pages that have no blank lines at all, only single-newline list items
    (verified on d5_..., d13_...) — is broken down further with the same
    separator cascade `chunk_recursive` uses, then pieces are merged back
    up to ~max_tokens.
    """
    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    pieces: list[str] = []
    for para in paragraphs:
        if count_tokens(para) <= max_tokens:
            pieces.append(para)
        else:
            pieces.extend(_split_recursive(para, ["\n", ". ", " "], max_tokens))

    chunks: list[RawChunk] = []
    idx = 0
    buf: list[str] = []
    for piece in pieces:
        candidate = "\n".join([*buf, piece])
        if buf and count_tokens(candidate) > max_tokens:
            chunks.append(RawChunk(chunk_index=idx, text="\n".join(buf), chunking_strategy=strategy))
            idx += 1
            buf = [piece]
        else:
            buf.append(piece)
    if buf:
        chunks.append(RawChunk(chunk_index=idx, text="\n".join(buf), chunking_strategy=strategy))
    return _finalize(chunks)


# --- Strategy 4: parent-child (Điều = parent, Khoản = child) -----------


def chunk_parent_child(text: str, max_child_tokens: int = 250) -> list[RawChunk]:
    """Emit parent chunks (whole Điều) followed by their child chunks
    (individual Khoản, `parent_index` pointing back at the parent's index
    in this same list). Documents without Điều headings fall back to
    paragraph chunking with no parent/child split (flat list, like
    structure_aware's fallback) — parent/child linking only makes sense
    where there is real Chương/Điều/Khoản hierarchy to link.
    """
    text = text.strip()
    if not text:
        return []

    sections = _split_by_dieu(text)
    if sections is None:
        return _chunk_paragraphs(text, max_child_tokens, strategy="parent_child")

    chunks: list[RawChunk] = []
    idx = 0
    for section_label, heading, body in sections:
        parent_idx = idx
        chunks.append(
            RawChunk(
                chunk_index=parent_idx,
                text=body,
                chunking_strategy="parent_child",
                section=section_label,
                heading=heading,
                metadata={"role": "parent"},
            )
        )
        idx += 1

        khoan_pairs = _split_khoan(body)
        if len(khoan_pairs) == 1 and not khoan_pairs[0][0]:
            # No numbered Khoản found inside this Điều — parent stands alone.
            continue

        for label, clause_text in khoan_pairs:
            # merge oversized single Khoản further isn't handled here — rare
            # in this corpus (verified: no Khoản in the IUH source set
            # exceeds max_child_tokens*2, see golden_set_review.md source
            # survey) and out of scope for a first Phase 3 pass.
            chunks.append(
                RawChunk(
                    chunk_index=idx,
                    text=clause_text,
                    chunking_strategy="parent_child",
                    section=f"{section_label}, Khoản {label}" if label else section_label,
                    heading=heading,
                    parent_index=parent_idx,
                    metadata={"role": "child"},
                )
            )
            idx += 1
    return _finalize(chunks)


CHUNKERS = {
    "fixed": chunk_fixed,
    "recursive": chunk_recursive,
    "structure_aware": chunk_structure_aware,
    "parent_child": chunk_parent_child,
}


def normalized_text_for(chunk: RawChunk) -> str:
    return normalize_for_search(chunk.text)
