from src.rag.citation import parse_model_output

CHUNKS = [
    {"chunk_id": "chunk_a", "document_id": "doc_1", "section": "Điều 6",
     "page_start": None, "text": "Nội dung điều sáu về tín chỉ." * 5},
    {"chunk_id": "chunk_b", "document_id": "doc_2", "section": None,
     "page_start": 3, "text": "Nội dung khác."},
]


def test_valid_json_with_valid_citation():
    raw = '{"answer": "Cần 2.0 điểm.", "citations": [{"chunk_id": "chunk_a"}], "refusal": false}'
    out = parse_model_output(raw, CHUNKS)
    assert not out.refusal
    assert out.answer == "Cần 2.0 điểm."
    assert [c.chunk_id for c in out.citations] == ["chunk_a"]
    assert out.citations[0].document_id == "doc_1"
    assert out.citations[0].section == "Điều 6"
    assert out.citations[0].quote  # trích đoạn để hiển thị nguồn


def test_markdown_fenced_json_is_parsed():
    raw = '```json\n{"answer": "OK", "citations": [{"chunk_id": "chunk_b"}], "refusal": false}\n```'
    out = parse_model_output(raw, CHUNKS)
    assert not out.refusal
    assert out.citations[0].chunk_id == "chunk_b"
    assert out.citations[0].page == 3


def test_fabricated_citation_is_dropped_and_flagged():
    raw = ('{"answer": "X", "citations": [{"chunk_id": "chunk_FAKE"}, '
           '{"chunk_id": "chunk_a"}], "refusal": false}')
    out = parse_model_output(raw, CHUNKS)
    assert [c.chunk_id for c in out.citations] == ["chunk_a"]
    assert out.invalid_citations == ["chunk_FAKE"]


def test_answer_with_only_fabricated_citations_downgrades_to_refusal():
    raw = '{"answer": "Bịa đấy", "citations": [{"chunk_id": "chunk_FAKE"}], "refusal": false}'
    out = parse_model_output(raw, CHUNKS, require_citation=True)
    assert out.refusal
    assert out.parse_error == "answer_without_valid_citation"
    assert "Bịa đấy" not in out.answer  # câu trả lời không nguồn không được lọt ra


def test_unparseable_output_refuses_safely():
    out = parse_model_output("xin chào, tôi không trả JSON đâu", CHUNKS)
    assert out.refusal
    assert out.parse_error == "unparseable_model_output"


def test_model_refusal_passthrough_with_default_message():
    raw = '{"answer": "", "citations": [], "refusal": true}'
    out = parse_model_output(raw, CHUNKS)
    assert out.refusal
    assert out.answer  # luôn có message cho user, không trả chuỗi rỗng


def test_duplicate_citations_deduped():
    raw = ('{"answer": "X", "citations": [{"chunk_id": "chunk_a"}, {"chunk_id": "chunk_a"}], '
           '"refusal": false}')
    out = parse_model_output(raw, CHUNKS)
    assert len(out.citations) == 1


# --- Ollama local fallback (qwen2.5:7b) đo thật 2026-07-13: model rút gọn
# chunk_id dài thành hậu tố ngắn (vd "chunk_doc_..._structure_aware_0060"
# -> "0060") thay vì chép nguyên văn — không phải context-window overflow
# (test cả num_ctx=4096/8192 ra kết quả giống hệt, xem CHECKLIST Phase 8).
# _resolve_chunk_id() cứu được các trường hợp hậu tố khớp DUY NHẤT 1 chunk
# trong tập đã retrieve, vẫn fail-closed khi mơ hồ hoặc quá ngắn.
_LONG_CHUNKS = [
    {"chunk_id": "chunk_doc_qd1482_quy_che_tin_chi_structure_aware_0060",
     "document_id": "doc_qd1482", "section": "Điều 12", "page_start": 5, "text": "Nội dung." * 5},
    {"chunk_id": "chunk_doc_sotay_2024_structure_aware_0007",
     "document_id": "doc_sotay", "section": None, "page_start": 2, "text": "Nội dung khác."},
]


def test_suffix_match_recovers_truncated_chunk_id():
    raw = '{"answer": "X", "citations": [{"chunk_id": "0060"}], "refusal": false}'
    out = parse_model_output(raw, _LONG_CHUNKS)
    assert not out.refusal
    assert [c.chunk_id for c in out.citations] == [
        "chunk_doc_qd1482_quy_che_tin_chi_structure_aware_0060"
    ]
    assert out.citations[0].document_id == "doc_qd1482"
    assert out.invalid_citations == []


def test_suffix_match_ambiguous_between_2_retrieved_chunks_stays_invalid():
    ambiguous_chunks = [
        {"chunk_id": "chunk_doc_a_structure_aware_0060", "document_id": "doc_a",
         "section": None, "page_start": None, "text": "A"},
        {"chunk_id": "chunk_doc_b_structure_aware_0060", "document_id": "doc_b",
         "section": None, "page_start": None, "text": "B"},
    ]
    raw = '{"answer": "X", "citations": [{"chunk_id": "0060"}], "refusal": false}'
    out = parse_model_output(raw, ambiguous_chunks)
    assert out.refusal  # không citation nào valid -> fail-closed
    assert out.invalid_citations == ["0060"]


def test_suffix_match_too_short_stays_invalid():
    raw = '{"answer": "X", "citations": [{"chunk_id": "60"}], "refusal": false}'
    out = parse_model_output(raw, _LONG_CHUNKS)
    assert out.refusal
    assert out.invalid_citations == ["60"]


def test_full_id_and_its_own_truncated_suffix_not_double_counted():
    raw = (
        '{"answer": "X", "citations": ['
        '{"chunk_id": "chunk_doc_qd1482_quy_che_tin_chi_structure_aware_0060"}, '
        '{"chunk_id": "0060"}], "refusal": false}'
    )
    out = parse_model_output(raw, _LONG_CHUNKS)
    assert len(out.citations) == 1
    assert out.citations[0].chunk_id == "chunk_doc_qd1482_quy_che_tin_chi_structure_aware_0060"
