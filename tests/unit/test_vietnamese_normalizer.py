from src.dataops.vietnamese_normalizer import (
    clean_text,
    clean_text_keep_pages,
    collapse_whitespace,
    extract_page_range,
    normalize_for_search,
    strip_ocr_artifacts,
    strip_page_sentinels,
    tag_pages,
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


def test_tag_pages_replaces_marker_with_sentinel():
    text = "--- Trang 5 ---\nĐiều 1. Nội dung"
    out = tag_pages(text)
    assert "[PG:5]" in out
    assert "Trang 5" not in out
    assert "Điều 1. Nội dung" in out


def test_tag_pages_still_drops_batch_markers():
    out = tag_pages("--- [batch trang 1-15/28] ---\n--- Trang 1 ---\nA")
    assert "batch" not in out


def test_tag_pages_offsets_batch_relative_page_numbers():
    """Real bug found via ingest dry-run on doc_sotay_2024 (82 pages, 6
    OCR batches): "Trang N" restarts at 1 every batch, so batch 2's
    "Trang 1" is actually absolute page 16, not page 1."""
    text = (
        "--- [batch trang 1-15/82] ---\n--- Trang 1 ---\nĐầu tài liệu\n"
        "--- [batch trang 16-30/82] ---\n--- Trang 1 ---\nGiữa tài liệu\n"
        "--- Trang 2 ---\nCuối đoạn"
    )
    out = tag_pages(text)
    assert "[PG:1]" in out  # batch 1's local page 1 -> absolute page 1
    assert "[PG:16]" in out  # batch 2's local page 1 -> absolute page 16
    assert "[PG:17]" in out  # batch 2's local page 2 -> absolute page 17
    assert "[PG:2]" not in out  # would be wrong: batch-local page 2, not offset
    assert "[PG:1]" in out


def test_extract_page_range_finds_min_and_max():
    text = "[PG:3] mở đầu\ncòn tiếp\n[PG:4] kết thúc"
    assert extract_page_range(text) == (3, 4)


def test_extract_page_range_single_page():
    assert extract_page_range("[PG:7] chỉ 1 trang") == (7, 7)


def test_extract_page_range_none_when_no_sentinel():
    assert extract_page_range("Không có marker trang nào ở đây") == (None, None)


def test_strip_page_sentinels_removes_tag_leaves_text():
    out = strip_page_sentinels("[PG:2] Điều 1. Phạm vi áp dụng")
    assert "[PG:" not in out
    assert "Điều 1. Phạm vi áp dụng" in out


def test_clean_text_keep_pages_preserves_sentinel_through_whitespace_collapse():
    text = "--- Trang 1 ---\nĐiều  1.   Phạm vi\n\n\n\náp dụng"
    out = clean_text_keep_pages(text)
    assert "[PG:1]" in out
    assert "Điều 1. Phạm vi" in out
    assert "\n\n\n" not in out
