"""Match golden-set expected_citations to real chunk_ids (Phase 4).

Solves the P0 gap noted in Phase 3 (CHECKLIST_IMPLEMENTATION.md, mục
"Chưa tốt / cần cải thiện"): naive exact-string matching of citation
sections against chunk sections only resolved 5/71 questions, because
structure_aware groups oversized Điều into Khoản-range chunks
("Điều 6, Khoản 4-6") while citations go to Điểm level
("Điều 6, Khoản 4.a").

Two matching paths, in priority order:

1. **Structural**: parse both the citation ("Điều 19, Khoản 1 và Khoản
   2.a" -> [(19,1), (19,2)]; "Điều 26, 27 (QĐ 610...)" -> [(26,None),
   (27,None)]) and the chunk section ("Điều 6, Khoản 4-6" -> dieu=6,
   khoản range [4,6]) and test coverage. Regexes require a digit after
   "Điều" — camnang headings like "Điều kiện xét tốt nghiệp" must NOT
   parse as an article number.
2. **Lexical fallback**: for documents whose chunks carry no section
   labels (camnang/sổ tay paragraph-fallback chunks — see chunker.py) or
   citations with no parseable article number, pick the chunk with the
   highest ground-truth token overlap, accepted only above a threshold.
   Matches found this way are flagged so reports can show how much of
   the mapping rests on the weaker heuristic.

A citation may legitimately match several chunks (duplicate Điều numbers
in QĐ 610's preamble vs quy chế body; a Khoản covered by both a range
chunk and a parent chunk). Metrics therefore treat each citation as a
GROUP of acceptable chunk_ids — covered if any one is retrieved — rather
than requiring every matched chunk (see src/retrieval/metrics.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.dataops.vietnamese_normalizer import tokenize

_CIT_DIEU_RE = re.compile(r"Điều\s+(\d+(?:\s*,\s*\d+)*)")
_CIT_KHOAN_RE = re.compile(r"Khoản\s+(\d+)")
_CHUNK_SECTION_RE = re.compile(r"^Điều\s+(\d+)(?:,\s*Khoản\s+(\d+)(?:-(\d+))?)?$")

LEXICAL_THRESHOLD = 0.45


@dataclass
class CitationMatch:
    """One expected_citation resolved to its acceptable chunk_ids."""

    document_id: str
    section: str
    chunk_ids: list[str] = field(default_factory=list)
    method: str = "none"  # structural | lexical | none


def parse_citation_section(section: str) -> list[tuple[int, int | None]]:
    """'Điều 19, Khoản 1 và Khoản 2.a' -> [(19, 1), (19, 2)].

    Returns [] when no article number is present (e.g. 'Bảng quy đổi
    điểm chứng chỉ tiếng Anh', 'Mục III.1, Hướng dẫn 05/HD-ĐHCN').
    """
    dieu_m = _CIT_DIEU_RE.search(section)
    if not dieu_m:
        return []
    dieu_numbers = [int(x) for x in re.findall(r"\d+", dieu_m.group(1))]
    khoan_numbers = [int(x) for x in _CIT_KHOAN_RE.findall(section)]

    if len(dieu_numbers) == 1 and khoan_numbers:
        return [(dieu_numbers[0], k) for k in khoan_numbers]
    return [(d, None) for d in dieu_numbers]


def parse_chunk_section(section: str | None) -> tuple[int, int | None, int | None] | None:
    """'Điều 6, Khoản 4-6' -> (6, 4, 6); 'Điều 6' -> (6, None, None)."""
    if not section:
        return None
    m = _CHUNK_SECTION_RE.match(section.strip())
    if not m:
        return None
    dieu = int(m.group(1))
    lo = int(m.group(2)) if m.group(2) else None
    hi = int(m.group(3)) if m.group(3) else lo
    return dieu, lo, hi


def _covers(chunk_sec: tuple[int, int | None, int | None], dieu: int, khoan: int | None) -> bool:
    c_dieu, lo, hi = chunk_sec
    if c_dieu != dieu:
        return False
    if lo is None:  # chunk holds the whole Điều
        return True
    if khoan is None:  # citation wants the whole Điều but chunk is a slice —
        return True  # any slice of the right Điều is acceptable evidence
    return lo <= khoan <= hi


def _lexical_best(ground_truth: str, chunks: list[dict]) -> tuple[str | None, float]:
    gt_tokens = set(tokenize(ground_truth))
    if not gt_tokens:
        return None, 0.0
    best_id, best_score = None, 0.0
    for chunk in chunks:
        overlap = len(gt_tokens & set(tokenize(chunk["text"]))) / len(gt_tokens)
        if overlap > best_score:
            best_id, best_score = chunk["chunk_id"], overlap
    return best_id, best_score


def match_citation(
    citation: dict,
    ground_truth: str,
    chunks_by_doc: dict[str, list[dict]],
) -> CitationMatch:
    doc_id = citation["document_id"]
    section = citation.get("section", "")
    result = CitationMatch(document_id=doc_id, section=section)
    doc_chunks = chunks_by_doc.get(doc_id, [])
    if not doc_chunks:
        return result

    targets = parse_citation_section(section)
    if targets:
        for chunk in doc_chunks:
            chunk_sec = parse_chunk_section(chunk.get("section"))
            if chunk_sec and any(_covers(chunk_sec, d, k) for d, k in targets):
                result.chunk_ids.append(chunk["chunk_id"])
        if result.chunk_ids:
            result.method = "structural"
            return result

    # No structural hit: either the citation has no article number, or the
    # document's chunks carry no parseable sections (paragraph fallback).
    best_id, score = _lexical_best(ground_truth, doc_chunks)
    if best_id is not None and score >= LEXICAL_THRESHOLD:
        result.chunk_ids.append(best_id)
        result.method = "lexical"
    return result


def match_question(
    item: dict,
    chunks_by_doc: dict[str, list[dict]],
) -> list[CitationMatch]:
    """All citation groups for one golden-set item (refusal items -> [])."""
    if item.get("requires_refusal"):
        return []
    return [
        match_citation(c, item.get("ground_truth", ""), chunks_by_doc)
        for c in item.get("expected_citations", [])
    ]


def group_chunks_by_document(chunks: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk["document_id"], []).append(chunk)
    return grouped
