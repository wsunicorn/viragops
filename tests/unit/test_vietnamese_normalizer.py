from src.dataops.vietnamese_normalizer import (
    clean_text,
    collapse_whitespace,
    normalize_for_search,
    strip_ocr_artifacts,
    tokenize,
)


def test_strip_ocr_artifacts_removes_page_and_batch_markers():
    text = "--- [batch trang 1-15/28] ---\n--- Trang 1 ---\nĐiều 1. Nội dung\n--- Trang 2 ---\nTiếp theo"
    out = strip_ocr_artifacts(text)
    assert "Trang 1" not in out
    assert "batch" not in out
    assert "Điều 1. Nội dung" in out
    assert "Tiếp theo" in out


def test_collapse_whitespace_merges_blank_lines_and_spaces():
    text = "A   B\n\n\n\nC\t\tD"
    out = collapse_whitespace(text)
    assert "   " not in out
    assert "\n\n\n" not in out


def test_clean_text_pipeline():
    text = "--- Trang 1 ---\nĐiều  1.   Phạm vi\n\n\n\náp dụng"
    out = clean_text(text)
    assert "Trang 1" not in out
    assert "Điều 1. Phạm vi" in out


def test_normalize_for_search_lowercases_but_keeps_diacritics():
    out = normalize_for_search("Điều Kiện TỐT NGHIỆP")
    assert out == "điều kiện tốt nghiệp"


def test_tokenize_splits_on_whitespace_and_punctuation():
    tokens = tokenize("Sinh viên, tích lũy đủ tín chỉ.")
    assert tokens == ["sinh", "viên", "tích", "lũy", "đủ", "tín", "chỉ"]
