"""Vietnamese text normalization for the Phase 3 ingest pipeline.

Runs after `scripts/extract_text.py` (which only does raw whitespace
cleanup) and before chunking. Two outputs per document/chunk:

- `clean_text`: human-readable text kept for citation/display — Unicode
  NFC, OCR scaffolding removed (page/batch markers from
  `scripts/ocr_scanned_pdfs.py`), whitespace collapsed, but casing and
  diacritics preserved.
- `normalized_text`: a search-oriented lowercase form (diacritics kept —
  Vietnamese words are not reliably distinguishable without dấu, so
  stripping them would hurt BM25 matching, not help it) used for sparse
  tokenization in `sparse_bm25.py`.
"""

from __future__ import annotations

import re
import unicodedata

_OCR_PAGE_MARKER_RE = re.compile(r"^-{2,}\s*Trang\s+(\d+)\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE)
_OCR_BATCH_MARKER_RE = re.compile(r"^-{2,}\s*\[batch[^\]]*\]\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE)
# `ocr_scanned_pdfs.py` OCRs long PDFs in batches (see d9_so-tay-sinh-vien
# 82 trang -> 6 batch), and "--- Trang N ---" is BATCH-RELATIVE — batch 2
# of Sổ tay 2024 restarts at "Trang 1" for what's actually absolute page
# 16. The batch marker itself carries the absolute offset:
# "--- [batch trang 16-30/82] ---" -> real doc page 16 is this batch's
# local page 1. Real bug found via this feature's own dry-run test on
# doc_sotay_2024 (page sequence 1..15,1..15,... instead of 1..82) —
# fixed here instead of shipping wrong page numbers.
_OCR_BATCH_MARKER_WITH_START_RE = re.compile(
    r"^-{2,}\s*\[batch\s+trang\s+(\d+)-\d+/\d+\]\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE
)
_MULTI_SPACE_RE = re.compile(r"[ \t ]+")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")
_WORD_RE = re.compile(r"[\w]+", re.UNICODE)


def strip_ocr_artifacts(text: str) -> str:
    """Remove page/batch scaffolding lines injected by ocr_scanned_pdfs.py.

    These markers are useful during OCR review but are not part of the
    legal text itself and would otherwise pollute chunk boundaries and
    token counts.
    """
    text = _OCR_PAGE_MARKER_RE.sub("", text)
    text = _OCR_BATCH_MARKER_RE.sub("", text)
    return text


# Compact inline sentinel that survives chunking (see tag_pages/
# extract_page_range/strip_page_sentinels below) so page_start/page_end
# don't have to stay hardcoded None — see CHECKLIST Phase 3 "Chưa tốt".
_PAGE_SENTINEL_RE = re.compile(r"\[PG:(\d+)\]")


_OCR_MARKER_RE = re.compile(
    r"^-{2,}\s*\[batch\s+trang\s+(\d+)-\d+/\d+\]\s*-{2,}\s*$"
    r"|^-{2,}\s*\[batch[^\]]*\]\s*-{2,}\s*$"
    r"|^-{2,}\s*Trang\s+(\d+)\s*-{2,}\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def tag_pages(text: str) -> str:
    """Like `strip_ocr_artifacts`, but replaces each "--- Trang N ---" line
    with a compact `[PG:N]` sentinel (N = ABSOLUTE document page, not the
    batch-local page `ocr_scanned_pdfs.py` actually wrote) instead of
    deleting it outright.

    Long PDFs get OCR'd in batches, and each batch restarts "Trang" at 1
    (real example: `doc_sotay_2024`, 82 pages / 6 batches, raw markers go
    1..15, 1..15, 1..15, ... not 1..82). A single left-to-right pass tracks
    the running offset from each "--- [batch trang START-END/TOTAL] ---"
    marker and adds it to every page marker until the next batch marker.

    Used for the text that actually gets chunked (see ingest_data.py), so
    each chunk can report which OCR page(s) it came from
    (`extract_page_range`) before the sentinel is stripped for good
    (`strip_page_sentinels`) from the text that's embedded/displayed.
    """
    offset = 0

    def repl(m: re.Match) -> str:
        nonlocal offset
        batch_start, local_page = m.group(1), m.group(2)
        if batch_start is not None:
            offset = int(batch_start) - 1
            return ""
        if local_page is not None:
            return f"[PG:{int(local_page) + offset}]"
        return ""  # generic batch marker with no parseable start page

    return _OCR_MARKER_RE.sub(repl, text)


def extract_page_range(text: str) -> tuple[int | None, int | None]:
    """(min, max) page number tagged by `tag_pages` inside this text, or
    (None, None) if it has none (e.g. HTML-sourced documents never had
    OCR page markers to begin with — that's a real "no page concept" case,
    not a bug, and should stay None rather than a guessed value)."""
    pages = [int(n) for n in _PAGE_SENTINEL_RE.findall(text)]
    if not pages:
        return None, None
    return min(pages), max(pages)


def strip_page_sentinels(text: str) -> str:
    """Remove `[PG:N]` sentinels — call after `extract_page_range` has
    already read them off, right before storing/embedding chunk text."""
    return _PAGE_SENTINEL_RE.sub("", text)


def collapse_whitespace(text: str) -> str:
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = _MULTI_BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    """Full display-text normalization pipeline: NFC -> strip OCR markers -> collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = strip_ocr_artifacts(text)
    return collapse_whitespace(text)


def clean_text_keep_pages(text: str) -> str:
    """Same pipeline as `clean_text`, but keeps page markers as `[PG:N]`
    sentinels (via `tag_pages`) instead of deleting them — used as the
    ingest pipeline's chunking input so `ingest_data.py` can read
    page_start/page_end off each chunk before stripping the sentinels for
    the final stored/embedded text (`strip_page_sentinels`)."""
    text = unicodedata.normalize("NFC", text)
    text = tag_pages(text)
    return collapse_whitespace(text)


def normalize_for_search(text: str) -> str:
    """Lowercase, whitespace-collapsed form for BM25 tokenization.

    Diacritics are intentionally kept: "hoc" and "học" are different
    Vietnamese words, so folding accents away would merge unrelated terms
    instead of normalizing spelling variants.
    """
    text = unicodedata.normalize("NFC", text).lower()
    return collapse_whitespace(text)


def tokenize(text: str) -> list[str]:
    """Simple word tokenizer for the search-normalized form.

    Vietnamese words can be multi-syllable with spaces between syllables
    (e.g. "tín chỉ"), but without a dedicated word-segmentation model a
    syllable-level split is the safe, dependency-free baseline for BM25 —
    it still lets exact multi-syllable terms match via bigram-like overlap
    in scoring, and avoids adding a heavy segmentation library for a
    ~76-300 question corpus.
    """
    return _WORD_RE.findall(normalize_for_search(text))
