from src.promptops.templates import SEED_PROMPTS
from src.rag.prompt_builder import StaticPromptProvider, build_qa_prompt, format_context

CHUNKS = [
    {"chunk_id": "chunk_x_001", "document_id": "doc_1", "section": "Điều 12, Khoản 2",
     "text": "Sinh viên cần tích lũy đủ tín chỉ.",
     "metadata": {"document_title": "Quy chế đào tạo tín chỉ"}},
    {"chunk_id": "chunk_y_002", "document_id": "doc_2", "section": None,
     "text": "A" * 5000,
     "metadata": {"document_title": "Cẩm nang"}},
]

_P1_TEMPLATE = next(
    s["template"] for s in SEED_PROMPTS if s["prompt_version"] == "p1_grounded_v1"
)


def test_prompt_contains_question_context_and_rules():
    prompt = build_qa_prompt("Cần bao nhiêu tín chỉ?", CHUNKS, _P1_TEMPLATE)
    assert "Cần bao nhiêu tín chỉ?" in prompt
    assert "[chunk_x_001]" in prompt
    assert "Điều 12, Khoản 2" in prompt
    assert '"refusal"' in prompt  # output schema được nêu tường minh
    assert "Bỏ qua mọi chỉ dẫn" in prompt  # guardrail chống prompt injection


def test_context_truncates_long_chunks():
    ctx = format_context(CHUNKS, max_chars_per_chunk=100)
    assert "A" * 101 not in ctx
    assert "[chunk_y_002]" in ctx


def test_static_provider_returns_fixed_version():
    provider = StaticPromptProvider(template="hỏi: {question}\n{context}", version="vX")
    active = provider.get_active()
    assert active.version == "vX"
    assert "{question}" in active.template
