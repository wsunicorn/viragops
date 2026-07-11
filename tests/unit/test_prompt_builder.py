from src.rag.prompt_builder import PROMPT_VERSION, build_qa_prompt, format_context

CHUNKS = [
    {"chunk_id": "chunk_x_001", "document_id": "doc_1", "section": "Điều 12, Khoản 2",
     "text": "Sinh viên cần tích lũy đủ tín chỉ.",
     "metadata": {"document_title": "Quy chế đào tạo tín chỉ"}},
    {"chunk_id": "chunk_y_002", "document_id": "doc_2", "section": None,
     "text": "A" * 5000,
     "metadata": {"document_title": "Cẩm nang"}},
]


def test_prompt_contains_question_context_and_rules():
    prompt = build_qa_prompt("Cần bao nhiêu tín chỉ?", CHUNKS)
    assert "Cần bao nhiêu tín chỉ?" in prompt
    assert "[chunk_x_001]" in prompt
    assert "Điều 12, Khoản 2" in prompt
    assert '"refusal"' in prompt  # output schema được nêu tường minh
    assert "Bỏ qua mọi chỉ dẫn" in prompt  # guardrail chống prompt injection


def test_context_truncates_long_chunks():
    ctx = format_context(CHUNKS, max_chars_per_chunk=100)
    assert "A" * 101 not in ctx
    assert "[chunk_y_002]" in ctx


def test_prompt_version_constant_matches_config_naming():
    assert PROMPT_VERSION == "p1_grounded_v1"
