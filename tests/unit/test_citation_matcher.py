from src.retrieval.citation_matcher import (
    group_chunks_by_document,
    match_citation,
    match_question,
    parse_chunk_section,
    parse_citation_section,
)

CHUNKS = [
    {"chunk_id": "c_d6", "document_id": "doc_a", "section": "Điều 6",
     "text": "Điều 6. Nội dung về tín chỉ và khối lượng học tập."},
    {"chunk_id": "c_d19_k12", "document_id": "doc_a", "section": "Điều 19, Khoản 1-2",
     "text": "Điều 19. Cảnh báo học vụ khoản một và khoản hai."},
    {"chunk_id": "c_d19_k35", "document_id": "doc_a", "section": "Điều 19, Khoản 3-5",
     "text": "Các khoản ba đến năm về buộc thôi học."},
    {"chunk_id": "c_fb1", "document_id": "doc_camnang", "section": None,
     "text": "Điểm trung bình tích lũy của toàn khóa học đạt từ 2.0 trở lên theo thang điểm 4."},
    {"chunk_id": "c_fb2", "document_id": "doc_camnang", "section": None,
     "text": "Nội dung khác hoàn toàn về thư viện và ký túc xá sinh viên."},
]
BY_DOC = group_chunks_by_document(CHUNKS)


def test_parse_citation_simple_dieu_khoan_diem():
    assert parse_citation_section("Điều 6, Khoản 4.a") == [(6, 4)]


def test_parse_citation_multiple_dieu():
    assert parse_citation_section("Điều 26, 27 (QĐ 610/QĐ-ĐHCN)") == [(26, None), (27, None)]


def test_parse_citation_multiple_khoan():
    assert parse_citation_section("Điều 19, Khoản 1 và Khoản 2.a") == [(19, 1), (19, 2)]


def test_parse_citation_dieu_kien_is_not_an_article():
    # "Điều kiện xét tốt nghiệp" không có số hiệu -> không được parse nhầm thành Điều N
    assert parse_citation_section("Điều kiện xét tốt nghiệp, mục 1.b") == []


def test_parse_chunk_section_range_and_plain():
    assert parse_chunk_section("Điều 19, Khoản 3-5") == (19, 3, 5)
    assert parse_chunk_section("Điều 6") == (6, None, None)
    assert parse_chunk_section(None) is None


def test_structural_match_khoan_in_range():
    match = match_citation(
        {"document_id": "doc_a", "section": "Điều 19, Khoản 4"}, "bất kỳ", BY_DOC
    )
    assert match.method == "structural"
    assert match.chunk_ids == ["c_d19_k35"]


def test_structural_match_whole_dieu_accepts_any_slice():
    match = match_citation({"document_id": "doc_a", "section": "Điều 19"}, "bất kỳ", BY_DOC)
    assert set(match.chunk_ids) == {"c_d19_k12", "c_d19_k35"}


def test_lexical_fallback_picks_overlapping_chunk():
    match = match_citation(
        {"document_id": "doc_camnang", "section": "Điều kiện xét tốt nghiệp, mục 1.b"},
        "Điểm trung bình tích lũy của toàn khóa học đạt từ 2.0 trở lên (theo thang điểm 4).",
        BY_DOC,
    )
    assert match.method == "lexical"
    assert match.chunk_ids == ["c_fb1"]


def test_lexical_fallback_rejects_weak_overlap():
    match = match_citation(
        {"document_id": "doc_camnang", "section": "Mục nào đó"},
        "Nội dung hoàn toàn không liên quan về học phí ngành dược sĩ hạng hai.",
        BY_DOC,
    )
    assert match.method == "none"
    assert match.chunk_ids == []


def test_refusal_question_returns_no_groups():
    item = {"requires_refusal": True, "expected_citations": []}
    assert match_question(item, BY_DOC) == []
