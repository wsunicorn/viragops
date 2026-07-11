from src.dataops.sparse_bm25 import BM25Sparse

CORPUS = [
    "Điều kiện tốt nghiệp cần tích lũy đủ tín chỉ theo chương trình đào tạo",
    "Học phí học kỳ được miễn giảm theo quy định của nhà nước",
    "Điều kiện tốt nghiệp yêu cầu chuẩn đầu ra tiếng Anh trình độ B1",
]


def test_fit_produces_idf_for_seen_terms():
    enc = BM25Sparse()
    enc.fit(CORPUS)
    assert enc.n_docs == 3
    assert enc.avgdl > 0
    assert len(enc.idf) > 0


def test_common_term_has_lower_idf_than_rare_term():
    enc = BM25Sparse()
    enc.fit(CORPUS)
    from src.dataops.sparse_bm25 import _hash_term

    idx_common = _hash_term("tốt", enc.vocab_size)  # appears in 2/3 docs
    idx_rare = _hash_term("miễn", enc.vocab_size)  # appears in 1/3 docs
    assert enc.idf.get(idx_rare, 0) > enc.idf.get(idx_common, 0)


def test_vectorize_document_nonempty_for_real_text():
    enc = BM25Sparse()
    enc.fit(CORPUS)
    vec = enc.vectorize_document(CORPUS[0])
    assert len(vec.indices) > 0
    assert len(vec.indices) == len(vec.values)
    assert all(v > 0 for v in vec.values)


def test_vectorize_empty_text_returns_empty_vector():
    enc = BM25Sparse()
    enc.fit(CORPUS)
    vec = enc.vectorize_document("")
    assert vec.indices == []
    assert vec.values == []


def test_state_roundtrip_produces_identical_query_vectors():
    enc = BM25Sparse()
    enc.fit(CORPUS)
    query = "điều kiện tốt nghiệp là gì"
    original = enc.vectorize_query(query)

    restored = BM25Sparse.from_state(enc.to_state())
    roundtrip = restored.vectorize_query(query)

    assert original.indices == roundtrip.indices
    assert original.values == roundtrip.values


def test_fit_on_empty_corpus_does_not_crash():
    enc = BM25Sparse()
    enc.fit([])
    assert enc.n_docs == 0
    vec = enc.vectorize_document("bất kỳ văn bản nào")
    assert vec.indices == []
