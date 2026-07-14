"""Unit test cho feedback clustering (Phase 11, Module 9)."""

from __future__ import annotations

from src.feedback.clustering import cluster_feedback
from src.feedback.schemas import FeedbackRecord


def _record(fid: str, trace_id: str, error_label: str | None, category: str | None) -> FeedbackRecord:
    return FeedbackRecord(
        feedback_id=fid, trace_id=trace_id, feedback_type="missing_citation",
        error_label=error_label, category=category,
    )


def test_groups_by_error_label_and_category():
    records = [
        _record("fb1", "t1", "citation_error", "multi_hop"),
        _record("fb2", "t2", "citation_error", "multi_hop"),
        _record("fb3", "t3", "citation_error", "ambiguous"),
        _record("fb4", "t4", "retrieval_failure", "multi_hop"),
    ]
    clusters = cluster_feedback(records)
    by_key = {(c.error_label, c.category): c.size for c in clusters}
    assert by_key[("citation_error", "multi_hop")] == 2
    assert by_key[("citation_error", "ambiguous")] == 1
    assert by_key[("retrieval_failure", "multi_hop")] == 1


def test_clusters_sorted_largest_first():
    records = [
        _record("fb1", "t1", "hallucination", "factoid"),
        _record("fb2", "t2", "citation_error", "multi_hop"),
        _record("fb3", "t3", "citation_error", "multi_hop"),
        _record("fb4", "t4", "citation_error", "multi_hop"),
    ]
    clusters = cluster_feedback(records)
    assert clusters[0].size >= clusters[1].size
    assert clusters[0].error_label == "citation_error"


def test_feedback_ids_preserved_per_cluster():
    records = [
        _record("fb1", "t1", "citation_error", "multi_hop"),
        _record("fb2", "t2", "citation_error", "multi_hop"),
    ]
    clusters = cluster_feedback(records)
    assert set(clusters[0].feedback_ids) == {"fb1", "fb2"}


def test_sample_questions_deduped_by_lexical_overlap():
    records = [
        _record("fb1", "t1", "citation_error", "multi_hop"),
        _record("fb2", "t2", "citation_error", "multi_hop"),
    ]
    questions = {
        "t1": "Điều kiện tốt nghiệp đại học là gì?",
        "t2": "Điều kiện tốt nghiệp đại học là gì vậy?",  # gần trùng t1
    }
    clusters = cluster_feedback(records, questions=questions)
    assert len(clusters[0].sample_questions) == 1


def test_sample_questions_capped_at_three():
    records = [_record(f"fb{i}", f"t{i}", "citation_error", "multi_hop") for i in range(5)]
    questions = {f"t{i}": f"Câu hỏi hoàn toàn khác nhau số {i} về học phí ký túc xá tín chỉ" for i in range(5)}
    clusters = cluster_feedback(records, questions=questions)
    assert len(clusters[0].sample_questions) <= 3


def test_no_questions_arg_gives_empty_samples():
    records = [_record("fb1", "t1", "citation_error", "multi_hop")]
    clusters = cluster_feedback(records)
    assert clusters[0].sample_questions == []
