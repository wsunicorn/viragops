from __future__ import annotations

from src.evaluation.metrics import citation_accuracy, context_precision


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
