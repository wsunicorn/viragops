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

_OCR_PAGE_MARKER_RE = re.compile(r"^-{2,}\s*Trang\s+\d+\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE)
_OCR_BATCH_MARKER_RE = re.compile(r"^-{2,}\s*\[batch[^\]]*\]\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE)
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
