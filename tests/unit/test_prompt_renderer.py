import pytest

from src.promptops.diff import prompt_diff
from src.promptops.renderer import RenderError, extract_variables, render, validate_template
from src.promptops.templates import COMMON_METADATA, SEED_PROMPTS


def test_extract_variables_ignores_escaped_json_braces():
    template = 'Trả về {{"answer": "..."}}. NGỮ CẢNH: {context}\nCÂU HỎI: {question}'
    assert extract_variables(template) == {"context", "question"}


def test_render_fills_variables_and_unescapes_braces():
    out = render('{{"x": 1}} hỏi: {question}', {"question": "vì sao?"})
    assert out == '{"x": 1} hỏi: vì sao?'


def test_render_missing_variable_raises():
    with pytest.raises(RenderError):
        render("hỏi: {question}", {})


def test_validate_template_catches_mismatch():
    with pytest.raises(RenderError, match="used but undeclared"):
        validate_template("{context} {extra}", ["context"])
    with pytest.raises(RenderError, match="declared but unused"):
        validate_template("{context}", ["context", "question"])


def test_all_seed_templates_valid_and_renderable():
    """Cả 9 variant P0-P8 phải render sạch với đúng bộ biến khai báo."""
    assert len(SEED_PROMPTS) == 9
    for seed in SEED_PROMPTS:
        validate_template(seed["template"], COMMON_METADATA["variables"])
        out = render(seed["template"], {"context": "[chunk_1] nội dung", "question": "hỏi gì?"})
        assert "[chunk_1] nội dung" in out
        assert "hỏi gì?" in out
        assert '"refusal"' in out  # mọi variant giữ chung JSON contract


def test_seed_versions_follow_naming_convention():
    versions = [s["prompt_version"] for s in SEED_PROMPTS]
    assert versions == [
        "p0_naive_v1", "p1_grounded_v1", "p2_citation_first_v1",
        "p3_refusal_aware_v1", "p4_self_check_v1", "p5_concise_v1",
        "p6_citation_complete_v1", "p7_citation_complete_safe_v1",
        "p8_citation_multipart_v1",
    ]


def test_prompt_diff_produces_unified_format():
    d = prompt_diff("dòng một\ndòng hai", "dòng một\ndòng ba", "p1", "p2")
    assert "--- p1" in d
    assert "+++ p2" in d
    assert "-dòng hai" in d
    assert "+dòng ba" in d


def test_prompt_diff_identical_templates_is_empty():
    assert prompt_diff("giống nhau", "giống nhau", "a", "b") == ""
