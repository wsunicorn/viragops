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
