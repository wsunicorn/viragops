from src.dataops.chunker import (
    chunk_fixed,
    chunk_parent_child,
    chunk_recursive,
    chunk_structure_aware,
    count_tokens,
)

SAMPLE_QUY_CHE = """Chương I
NHỮNG QUY ĐỊNH CHUNG

Điều 1. Phạm vi điều chỉnh
1. Quy chế này quy định về đào tạo.
2. Áp dụng cho toàn trường.

Điều 2. Điều kiện tốt nghiệp
1. Sinh viên phải tích lũy đủ tín chỉ.
2. Điểm trung bình tích lũy đạt từ 2.0 trở lên.
a) Áp dụng thang điểm 4.
b) Trường hợp đặc biệt do hội đồng xét.
3. Đạt chuẩn đầu ra tiếng Anh.

Chương II
TỔ CHỨC THI

Điều 3. Hình thức thi
1. Thi viết hoặc thi vấn đáp.
"""

NO_HEADING_TEXT = """Điều kiện xét tốt nghiệp - Cẩm nang người học
1. Sinh viên được xét tốt nghiệp khi có đủ điều kiện sau:
a) Tích lũy đủ tín chỉ.
b) Điểm trung bình đạt 2.0.
2. Sinh viên hết thời gian học tối đa được gia hạn.
"""


def test_structure_aware_splits_by_dieu_and_keeps_khoan_together():
    chunks = chunk_structure_aware(SAMPLE_QUY_CHE, max_tokens=600)
    sections = [c.section for c in chunks]
    assert sections == ["Điều 1", "Điều 2", "Điều 3"]
    dieu2 = chunks[1]
    assert "tín chỉ" in dieu2.text
    assert "thang điểm 4" in dieu2.text  # Khoản 2's sub-điểm a) stayed inside Điều 2
    assert "Chương I" in dieu2.heading
    assert "Chương II" in chunks[2].heading


def test_structure_aware_falls_back_to_paragraphs_without_dieu_heading():
    chunks = chunk_structure_aware(NO_HEADING_TEXT, max_tokens=600)
    assert len(chunks) >= 1
    assert all(c.section is None for c in chunks)
    assert all(c.chunking_strategy == "structure_aware" for c in chunks)
    full_text = "\n".join(c.text for c in chunks)
    assert "Tích lũy đủ tín chỉ" in full_text


def test_structure_aware_splits_oversized_dieu_by_khoan():
    long_dieu = "Điều 9. Điều dài\n" + "\n".join(
        f"{i}. Nội dung khoản số {i} lặp lại nhiều lần để tăng độ dài văn bản test. " * 3
        for i in range(1, 30)
    )
    chunks = chunk_structure_aware(long_dieu, max_tokens=200)
    assert len(chunks) > 1
    assert all(c.section.startswith("Điều 9") for c in chunks)
    assert all(c.token_count <= 260 for c in chunks)  # some slack for the merge boundary


def test_parent_child_links_children_to_parent_by_index():
    chunks = chunk_parent_child(SAMPLE_QUY_CHE, max_child_tokens=250)
    parents = [c for c in chunks if c.parent_index is None]
    children = [c for c in chunks if c.parent_index is not None]
    assert len(parents) == 3  # Điều 1, 2, 3

    dieu2_parent = next(c for c in parents if c.section == "Điều 2")
    dieu2_children = [c for c in children if c.parent_index == dieu2_parent.chunk_index]
    assert len(dieu2_children) == 3  # Khoản 1, 2, 3
    assert dieu2_children[0].section == "Điều 2, Khoản 1"

    dieu3_parent = next(c for c in parents if c.section == "Điều 3")
    dieu3_children = [c for c in children if c.parent_index == dieu3_parent.chunk_index]
    assert len(dieu3_children) == 1


def test_parent_child_falls_back_without_dieu_heading():
    chunks = chunk_parent_child(NO_HEADING_TEXT, max_child_tokens=250)
    assert all(c.parent_index is None for c in chunks)
    assert all(c.chunking_strategy == "parent_child" for c in chunks)


def test_fixed_chunking_respects_window_and_overlap():
    text = " ".join(f"từ{i}" for i in range(500))
    chunks = chunk_fixed(text, chunk_size_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= 100
        assert c.chunking_strategy == "fixed"


def test_recursive_chunking_merges_small_pieces_up_to_budget():
    text = "\n\n".join(f"Đoạn văn số {i} nói về quy chế đào tạo tín chỉ." for i in range(50))
    chunks = chunk_recursive(text, chunk_size_tokens=100, overlap_tokens=10)
    assert len(chunks) > 1
    assert all(c.chunking_strategy == "recursive" for c in chunks)


def test_empty_text_returns_no_chunks():
    assert chunk_fixed("") == []
    assert chunk_recursive("   ") == []
    assert chunk_structure_aware("") == []
    assert chunk_parent_child("") == []


def test_count_tokens_nonzero_for_real_text():
    assert count_tokens("Điều kiện tốt nghiệp đại học") > 0
    assert count_tokens("") == 0
