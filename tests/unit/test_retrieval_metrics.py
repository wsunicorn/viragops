import math

from src.retrieval.metrics import aggregate, evaluate_question


def test_perfect_retrieval_scores_one():
    ev = evaluate_question(["a", "b"], [{"a"}, {"b"}], k=5)
    assert ev.recall_at_k == 1.0
    assert ev.hit_at_k == 1.0
    assert ev.mrr == 1.0
    assert ev.ndcg_at_k == 1.0
    assert ev.first_hit_rank == 1


def test_no_relevant_retrieved_scores_zero():
    ev = evaluate_question(["x", "y", "z"], [{"a"}], k=5)
    assert ev.recall_at_k == 0.0
    assert ev.hit_at_k == 0.0
    assert ev.mrr == 0.0
    assert ev.ndcg_at_k == 0.0
    assert ev.first_hit_rank is None


def test_group_covered_by_any_member_not_all():
    # 1 citation có 2 chunk chấp nhận được (Điều trùng số/parent+child):
    # lấy được 1 trong 2 là ĐỦ — không bị phạt vì thiếu bản trùng.
    ev = evaluate_question(["dup_2"], [{"dup_1", "dup_2"}], k=5)
    assert ev.recall_at_k == 1.0


def test_recall_counts_covered_citations_fraction():
    ev = evaluate_question(["a", "x", "y", "z", "w"], [{"a"}, {"b"}], k=5)
    assert ev.recall_at_k == 0.5


def test_mrr_uses_full_list_beyond_k():
    ev = evaluate_question(["x", "y", "z", "w", "v", "a"], [{"a"}], k=5)
    assert ev.hit_at_k == 0.0  # ngoài top-5
    assert ev.mrr == 1.0 / 6  # nhưng MRR vẫn tính theo rank thật
    assert ev.first_hit_rank == 6


def test_ndcg_no_double_credit_for_same_citation():
    # 2 chunk cùng cover 1 citation duy nhất -> chỉ chunk đầu được gain
    ev = evaluate_question(["dup_1", "dup_2"], [{"dup_1", "dup_2"}], k=5)
    assert ev.ndcg_at_k == 1.0  # dcg = 1/log2(2), idcg = 1/log2(2)


def test_ndcg_rank_position_matters():
    ev = evaluate_question(["x", "a"], [{"a"}], k=5)
    expected = (1 / math.log2(3)) / (1 / math.log2(2))
    assert abs(ev.ndcg_at_k - expected) < 1e-9


def test_question_without_citations_excluded():
    assert evaluate_question(["a"], [], k=5) is None
    assert evaluate_question(["a"], [set()], k=5) is None


def test_aggregate_averages():
    e1 = evaluate_question(["a"], [{"a"}], k=5)
    e2 = evaluate_question(["x"], [{"a"}], k=5)
    agg = aggregate([e1, e2])
    assert agg["n_questions"] == 2
    assert agg["recall_at_k"] == 0.5
    assert agg["hit_rate"] == 0.5
