from __future__ import annotations

from src.evaluation.metrics import ambiguity_handled, citation_accuracy, context_precision


def test_context_precision_basic():
    assert context_precision(["a", "b", "c"], [{"a"}, {"z"}]) == 1 / 3


def test_context_precision_none_when_no_groups():
    assert context_precision(["a"], []) is None


def test_context_precision_none_when_nothing_retrieved():
    assert context_precision([], [{"a"}]) is None


def test_context_precision_none_when_groups_all_empty():
    assert context_precision(["a"], [set()]) is None


def test_citation_accuracy_basic():
    assert citation_accuracy(["a", "b"], [{"a"}, {"c"}]) == 0.5


def test_citation_accuracy_all_correct():
    assert citation_accuracy(["a"], [{"a", "b"}]) == 1.0


def test_citation_accuracy_none_when_nothing_cited():
    assert citation_accuracy([], [{"a"}]) is None


def test_citation_accuracy_none_when_no_groups():
    assert citation_accuracy(["a"], []) is None


def test_ambiguity_handled_clarifying_question():
    answer = "Bạn có thể cho biết học phần bị rớt là bắt buộc hay tự chọn không?"
    assert ambiguity_handled(answer) is True


def test_ambiguity_handled_multi_branch_coverage():
    answer = (
        "Nếu đây là học phần bắt buộc thì áp dụng Điều 12 Khoản 1; còn nếu là "
        "học phần tự chọn thì áp dụng Khoản 2, tùy trường hợp sinh viên chọn "
        "học lại hay học cải thiện."
    )
    assert ambiguity_handled(answer) is True


def test_ambiguity_handled_false_when_single_branch_committed():
    answer = "Sinh viên bị rớt môn phải đăng ký học lại học phần đó trong học kỳ kế tiếp."
    assert ambiguity_handled(answer) is False


def test_ambiguity_handled_false_on_lone_branch_marker():
    # 1 marker duy nhất không đủ để coi là bao quát nhiều nhánh — tránh false
    # positive từ câu văn thông thường có chứa "nếu"/"hoặc" 1 lần.
    answer = "Nếu cần hỗ trợ thêm, sinh viên có thể liên hệ phòng đào tạo."
    assert ambiguity_handled(answer) is False
