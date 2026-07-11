from src.dataops.quality_checker import check_chunks, summarize_by_document


def _chunk(**overrides):
    base = {
        "chunk_id": "chunk_001",
        "document_id": "doc_a",
        "text": "Điều 1. Nội dung hợp lệ đủ dài để không bị cảnh báo ngắn quá mức tối thiểu.",
        "token_count": 20,
        "section": "Điều 1",
        "chunking_strategy": "structure_aware",
    }
    base.update(overrides)
    return base


def test_empty_text_is_critical():
    report = check_chunks([_chunk(text="")])
    assert not report.is_critical_clean
    assert any(e["error"] == "empty_text" for e in report.critical_errors)


def test_missing_document_id_is_critical():
    report = check_chunks([_chunk(document_id=None)])
    assert any(e["error"] == "missing_document_id" for e in report.critical_errors)


def test_duplicate_chunk_id_is_critical():
    report = check_chunks([_chunk(chunk_id="x"), _chunk(chunk_id="x")])
    assert any(e["error"] == "duplicate_chunk_id" for e in report.critical_errors)


def test_short_and_long_chunks_are_warnings_not_critical():
    report = check_chunks(
        [_chunk(chunk_id="a", token_count=3), _chunk(chunk_id="b", token_count=5000)],
        min_tokens=15,
        max_tokens=1200,
    )
    assert report.is_critical_clean
    warning_types = {w.get("warning") for w in report.warnings}
    assert "chunk_too_short" in warning_types
    assert "chunk_too_long" in warning_types


def test_duplicate_content_flagged_as_warning():
    report = check_chunks(
        [_chunk(chunk_id="a", text="Cùng nội dung hệt nhau lặp lại đủ dài."),
         _chunk(chunk_id="b", text="Cùng nội dung hệt nhau lặp lại đủ dài.")]
    )
    assert report.is_critical_clean
    assert any(w.get("warning") == "duplicate_content" for w in report.warnings)


def test_fallback_chunk_without_section_not_flagged_for_fixed_strategy():
    report = check_chunks([_chunk(section=None, chunking_strategy="fixed")])
    assert not any(w.get("warning") == "missing_section" for w in report.warnings)


def test_summarize_by_document_counts_per_doc():
    chunks = [_chunk(chunk_id="a", document_id="doc_a"), _chunk(chunk_id="b", document_id="doc_a"),
              _chunk(chunk_id="c", document_id="doc_b")]
    counts = summarize_by_document(chunks)
    assert counts == {"doc_a": 2, "doc_b": 1}
