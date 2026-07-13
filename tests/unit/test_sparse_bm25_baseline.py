"""Validates src/dataops/sparse_bm25.py's scoring FORMULA against
rank_bm25's BM25Okapi (a well-established reference implementation) —
closes the "chưa so sánh với 1 baseline đã biết đúng" gap noted in
CHECKLIST Phase 3 "Chưa tốt".

Both implementations are fed the SAME already-tokenized text (our own
`tokenize()`), so this isolates "is the BM25 math right" from "does the
hashing trick or the Vietnamese tokenizer introduce noise" (separate,
already-tested concerns — see test_sparse_bm25.py and
test_vietnamese_normalizer.py).

Exact score VALUES are not expected to match: rank_bm25's BM25Okapi uses
the ATIRE idf variant (epsilon floor), while sparse_bm25.py uses the
classic Robertson/Sparck-Jones `log(1 + ...)` idf — both are legitimate,
standard BM25 variants that only differ in how they floor idf for
very-common terms, not in the ranking behaviour this test checks.
"""

from __future__ import annotations

from rank_bm25 import BM25Okapi

from src.dataops.sparse_bm25 import BM25Sparse
from src.dataops.vietnamese_normalizer import tokenize

CORPUS = [
    "Điều kiện tốt nghiệp cần tích lũy đủ tín chỉ theo chương trình đào tạo",
    "Học phí học kỳ được miễn giảm theo quy định của nhà nước đối với sinh viên khó khăn",
    "Sinh viên bị cảnh báo kết quả học tập nếu điểm trung bình chung học kỳ quá thấp",
    "Chuẩn đầu ra tiếng Anh yêu cầu chứng chỉ quốc tế trình độ B1 trở lên",
    "Thời gian đào tạo đại học chính quy tối đa không quá 8 năm học",
    "Sinh viên đăng ký học phần trực tuyến qua hệ thống LMS của nhà trường",
    "Kỷ luật sinh viên vi phạm quy chế thi cử có thể bị đình chỉ học tập",
    "Học bổng khuyến khích học tập xét theo điểm trung bình và kết quả rèn luyện",
]

# Each query's tokens overlap most strongly and unambiguously with exactly
# one CORPUS document (by construction) — a correct BM25 implementation
# should rank that document #1 regardless of idf-variant details.
QUERIES_WITH_EXPECTED_TOP_DOC = [
    ("điều kiện tốt nghiệp tích lũy tín chỉ", 0),
    ("học phí miễn giảm sinh viên khó khăn", 1),
    ("cảnh báo kết quả học tập điểm trung bình", 2),
    ("chuẩn đầu ra tiếng anh chứng chỉ B1", 3),
    ("thời gian đào tạo tối đa 8 năm", 4),
    ("đăng ký học phần trực tuyến LMS", 5),
    ("kỷ luật vi phạm quy chế thi cử đình chỉ", 6),
    ("học bổng khuyến khích học tập rèn luyện", 7),
]


def _our_ranking(query: str) -> list[int]:
    enc = BM25Sparse()
    enc.fit(CORPUS)
    doc_vecs = [enc.vectorize_document(d) for d in CORPUS]
    query_vec = enc.vectorize_query(query)
    q_weight = dict(zip(query_vec.indices, query_vec.values, strict=True))

    scores = []
    for vec in doc_vecs:
        score = sum(q_weight.get(idx, 0.0) * val for idx, val in zip(vec.indices, vec.values, strict=True))
        scores.append(score)
    return sorted(range(len(CORPUS)), key=lambda i: scores[i], reverse=True)


def _reference_ranking(query: str) -> list[int]:
    tokenized_corpus = [tokenize(d) for d in CORPUS]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenize(query))
    return sorted(range(len(CORPUS)), key=lambda i: scores[i], reverse=True)


def test_top_ranked_document_matches_reference_for_every_query():
    for query, expected_doc in QUERIES_WITH_EXPECTED_TOP_DOC:
        our_top = _our_ranking(query)[0]
        ref_top = _reference_ranking(query)[0]
        assert our_top == expected_doc, f"our impl ranked doc {our_top} first for {query!r}, expected {expected_doc}"
        assert ref_top == expected_doc, f"reference impl ranked doc {ref_top} first for {query!r}, expected {expected_doc} (sanity check on the test corpus itself)"


def test_full_ranking_order_matches_reference_closely():
    """Not just top-1 — the full document ordering should agree on most
    positions between our impl and the reference, for every query."""
    mismatches_total = 0
    positions_total = 0
    for query, _ in QUERIES_WITH_EXPECTED_TOP_DOC:
        our = _our_ranking(query)
        ref = _reference_ranking(query)
        our_rank = {doc: i for i, doc in enumerate(our)}
        ref_rank = {doc: i for i, doc in enumerate(ref)}
        for doc in range(len(CORPUS)):
            positions_total += 1
            if abs(our_rank[doc] - ref_rank[doc]) > 1:  # allow +/-1 rank drift
                mismatches_total += 1

    mismatch_rate = mismatches_total / positions_total
    assert mismatch_rate <= 0.15, f"ranking diverges from rank_bm25 reference in {mismatch_rate:.0%} of positions"
