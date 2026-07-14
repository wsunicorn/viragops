"""Unit test cho extractive context compression (Phase 11, Module 8)."""

from __future__ import annotations

from src.optimization.compression import compress_chunk_text, compress_chunks


def test_short_text_unchanged():
    text = "Điều 6. Sinh viên phải đạt điểm trung bình tích lũy 2.0."
    assert compress_chunk_text(text, "điểm trung bình tích lũy", max_chars=200) == text


def test_long_text_compressed_below_budget_ish():
    text = (
        "Điều 6. Sinh viên phải đạt điểm trung bình tích lũy 2.0 để tốt nghiệp. "
        "Ngoài ra sinh viên cần hoàn thành đủ số tín chỉ theo chương trình đào tạo. "
        "Nhà trường tổ chức lễ tốt nghiệp mỗi năm hai lần vào tháng 6 và tháng 12. "
        "Sinh viên cần nộp đơn xét tốt nghiệp trước thời hạn quy định của phòng đào tạo."
    )
    compressed = compress_chunk_text(text, "điểm trung bình tích lũy tốt nghiệp", max_chars=100)
    assert len(compressed) < len(text)


def test_compression_keeps_sentence_most_relevant_to_query():
    text = (
        "Nhà trường tổ chức lễ tốt nghiệp mỗi năm hai lần. "
        "Điểm trung bình tích lũy tối thiểu để tốt nghiệp là 2.0 theo thang điểm 4."
    )
    compressed = compress_chunk_text(text, "điểm trung bình tích lũy", max_chars=60)
    assert "2.0" in compressed


_LONG_MULTI_SENTENCE = (
    "Điều 6. Sinh viên phải đạt điểm trung bình tích lũy 2.0 để tốt nghiệp. "
    "Ngoài ra sinh viên cần hoàn thành đủ số tín chỉ theo chương trình đào tạo. "
    "Nhà trường tổ chức lễ tốt nghiệp mỗi năm hai lần vào tháng 6 và tháng 12. "
    "Sinh viên cần nộp đơn xét tốt nghiệp trước thời hạn quy định của phòng đào tạo."
)


def test_compress_chunks_preserves_other_fields():
    chunks = [
        {"chunk_id": "c1", "text": _LONG_MULTI_SENTENCE, "document_id": "doc1", "score": 1.5},
    ]
    compressed = compress_chunks(chunks, "điểm trung bình tích lũy", max_chars=100)
    assert compressed[0]["chunk_id"] == "c1"
    assert compressed[0]["document_id"] == "doc1"
    assert compressed[0]["score"] == 1.5
    assert len(compressed[0]["text"]) < len(_LONG_MULTI_SENTENCE)


def test_compress_chunks_does_not_mutate_original():
    chunks = [{"chunk_id": "c1", "text": _LONG_MULTI_SENTENCE}]
    compress_chunks(chunks, "điểm trung bình tích lũy", max_chars=100)
    assert chunks[0]["text"] == _LONG_MULTI_SENTENCE
