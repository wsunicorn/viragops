"""Eval report writer (Phase 8, Module 5) — CSV per-question detail +
Markdown aggregate/category/failure report, mirroring the CSV+Markdown
pattern Phase 4's scripts/run_experiment.py established (MLflow/DVC are
named as storage in modules/05_evaluation_engine.md but were never wired
up anywhere in this codebase — CSV/Markdown is what's actually true, so
that's what this writes, consistent with the project's no-fabrication rule).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.evaluation.runner import QuestionResult, aggregate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = PROJECT_ROOT / "data" / "eval"
RESULTS_DOC_DIR = PROJECT_ROOT / "docs" / "system" / "experiments"

TARGETS = {
    "recall_at_k": 0.85,
    "context_precision": 0.75,
    "context_recall": 0.80,
    "context_relevance": 0.80,
    "faithfulness": 0.85,
    "answer_relevance": 0.80,
    "citation_accuracy": 0.85,
    "refusal_accuracy": 0.90,
    "hallucination_rate": 0.05,  # <= target, not >=
    "p95_latency_ms": 6000,
}


def _fmt(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:.3f}" if abs(x) < 10 else f"{x:.0f}"


def _verdict(key: str, value: float | None) -> str:
    if value is None or key not in TARGETS:
        return ""
    target = TARGETS[key]
    if key in ("hallucination_rate",):
        return "ĐẠT" if value <= target else "CHƯA ĐẠT"
    if key == "p95_latency_ms":
        return "ĐẠT" if value <= target else "CHƯA ĐẠT"
    return "ĐẠT" if value >= target else "CHƯA ĐẠT"


def _category_breakdown(results: list[QuestionResult]) -> list[dict]:
    by_cat: dict[str, list[QuestionResult]] = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)
    rows = []
    for cat, items in sorted(by_cat.items()):
        agg = aggregate(items)
        rows.append({"category": cat, "n": len(items), **agg})
    return rows


def _failure_cases(results: list[QuestionResult], limit: int = 30) -> list[dict]:
    failures = []
    for r in results:
        reasons = []
        if not r.refusal_correct:
            reasons.append(
                "refusal_sai (kỳ vọng refusal="
                f"{r.requires_refusal}, thực tế={r.got_refusal})"
            )
        if r.retrieval_eval is not None and r.retrieval_eval.hit_at_k == 0:
            reasons.append("retrieval_miss (hit@k=0)")
        if r.citation_accuracy is not None and r.citation_accuracy < 1.0:
            reasons.append(f"citation_sai ({r.citation_accuracy:.2f})")
        if r.judge and "error" not in r.judge:
            if r.judge["faithfulness"] < 1.0:
                reasons.append(f"faithfulness={r.judge['faithfulness']}")
            if r.judge["hallucination"]:
                reasons.append("hallucination")
        if r.judge and "error" in r.judge:
            reasons.append("judge_error")
        if r.ambiguity_handled is False:
            reasons.append("ambiguity_unhandled (chốt 1 nhánh, không hỏi lại/bao quát)")
        if r.error_labels:
            reasons.append("trace_error:" + ",".join(r.error_labels))
        if reasons:
            failures.append(
                {
                    "question_id": r.question_id,
                    "category": r.category,
                    "question": r.question,
                    "reasons": "; ".join(reasons),
                }
            )
    return failures[:limit]


def _fallback_note(results: list[QuestionResult]) -> list[str]:
    """Nếu gateway rơi khỏi 'primary' (rate-limit/quota cạn giữa run — quan
    sát thật 2026-07-12: 35/298 câu ở cuối 1 lần full eval), số liệu tổng
    hợp bị nhiễu bởi model fallback (thường chậm hơn và hay bị hạ refusal
    do citation không hợp lệ) — tách riêng để không đọc nhầm gap hạ tầng
    thành gap chất lượng retrieval/prompt."""
    non_primary = [r for r in results if r.fallback_hop not in ("primary", "n/a", "unknown", None)]
    if not non_primary:
        return []
    primary = [r for r in results if r.fallback_hop == "primary"]
    if not primary:
        return []

    p_agg, f_agg = aggregate(primary), aggregate(non_primary)
    pct = len(non_primary) / len(results)
    return [
        f"> **⚠️ {len(non_primary)}/{len(results)} câu ({pct:.1%}) bị phục vụ bởi fallback "
        "hop (không phải model primary)** — thường do quota/rate-limit cạn giữa run dài. "
        "Số liệu tổng hợp phía trên gồm cả các câu này; bảng dưới tách riêng để không đọc "
        "nhầm nhiễu hạ tầng thành gap chất lượng retrieval/prompt:",
        "",
        "| Nhóm | n | Recall@k | Citation Acc | Refusal Acc | Faithfulness | p95 latency |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| primary | {len(primary)} | {_fmt(p_agg['retrieval'].get('recall_at_k'))} | "
        f"{_fmt(p_agg['citation_accuracy'])} | {_fmt(p_agg['refusal_accuracy'])} | "
        f"{_fmt(p_agg['faithfulness'])} | {p_agg['p95_latency_ms']} ms |",
        f"| fallback | {len(non_primary)} | {_fmt(f_agg['retrieval'].get('recall_at_k'))} | "
        f"{_fmt(f_agg['citation_accuracy'])} | {_fmt(f_agg['refusal_accuracy'])} | "
        f"{_fmt(f_agg['faithfulness'])} | {f_agg['p95_latency_ms']} ms |",
        "",
    ]


def write_csv(mode: str, results: list[QuestionResult], ts: str) -> Path:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = EVAL_DIR / f"eval_{mode}_{ts}.csv"
    cols = [
        "question_id", "category", "requires_refusal", "got_refusal", "refusal_correct",
        "recall_at_k", "hit_at_k", "mrr", "ndcg_at_k", "context_precision", "citation_accuracy",
        "faithfulness", "answer_relevance", "context_relevance", "hallucination",
        "judge2_faithfulness", "judge2_answer_relevance", "judge2_context_relevance",
        "judge2_hallucination", "ambiguity_handled",
        "latency_ms", "cost_usd", "fallback_hop", "error_labels",
    ]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in results:
            j = r.judge or {}
            j2 = r.judge2 or {}
            row = {
                "question_id": r.question_id,
                "category": r.category,
                "requires_refusal": r.requires_refusal,
                "got_refusal": r.got_refusal,
                "refusal_correct": r.refusal_correct,
                "recall_at_k": r.retrieval_eval.recall_at_k if r.retrieval_eval else "",
                "hit_at_k": r.retrieval_eval.hit_at_k if r.retrieval_eval else "",
                "mrr": r.retrieval_eval.mrr if r.retrieval_eval else "",
                "ndcg_at_k": r.retrieval_eval.ndcg_at_k if r.retrieval_eval else "",
                "context_precision": r.context_precision if r.context_precision is not None else "",
                "citation_accuracy": r.citation_accuracy if r.citation_accuracy is not None else "",
                "faithfulness": j.get("faithfulness", ""),
                "answer_relevance": j.get("answer_relevance", ""),
                "context_relevance": j.get("context_relevance", ""),
                "hallucination": j.get("hallucination", ""),
                "judge2_faithfulness": j2.get("faithfulness", ""),
                "judge2_answer_relevance": j2.get("answer_relevance", ""),
                "judge2_context_relevance": j2.get("context_relevance", ""),
                "judge2_hallucination": j2.get("hallucination", ""),
                "ambiguity_handled": r.ambiguity_handled if r.ambiguity_handled is not None else "",
                "latency_ms": r.latency_ms,
                "cost_usd": r.cost_usd,
                "fallback_hop": r.fallback_hop,
                "error_labels": "|".join(r.error_labels),
            }
            f.write(",".join(str(row[c]) for c in cols) + "\n")
    return csv_path


def write_markdown(
    mode: str, results: list[QuestionResult], meta: dict[str, Any], ts: str, eval_k: int = 5
) -> Path:
    overall = aggregate(results, eval_k=eval_k)
    ret = overall.get("retrieval", {})

    lines = [
        f"# Eval report — mode={mode}",
        "",
        f"> Sinh bởi `scripts/run_evaluation.py` lúc {ts} UTC. "
        f"data_version=`{meta.get('data_version')}`, index_version=`{meta.get('index_version')}`, "
        f"retrieval_config_id=`{meta.get('retrieval_config_id')}`, "
        f"prompt_version=`{meta.get('prompt_version')}`. "
        f"Số câu chạy: {overall['n_questions']}. "
        "Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, "
        f"câu không-refusal tốn thêm 1 lệnh judge thật ({overall.get('n_judged', 0)} câu đã "
        f"chấm, {overall.get('n_judge_errors', 0)} lỗi parse judge).",
        "",
        "## Kết quả tổng hợp",
        "",
        "| Metric | Giá trị | Target | Verdict |",
        "|---|---:|---:|---|",
    ]

    def row(label: str, key: str, value: float | None) -> str:
        target = TARGETS.get(key)
        return f"| {label} | {_fmt(value)} | {_fmt(target)} | {_verdict(key, value)} |"

    lines += [
        row(f"Recall@{overall.get('eval_k', 5)}", "recall_at_k", ret.get("recall_at_k")),
        f"| Hit rate | {_fmt(ret.get('hit_rate'))} | | |",
        f"| MRR | {_fmt(ret.get('mrr'))} | | |",
        row("Context Precision", "context_precision", overall["context_precision"]),
        row("Context Recall", "context_recall", overall["context_recall"]),
        row("Context Relevance (judge)", "context_relevance", overall["context_relevance"]),
        row("Faithfulness (judge)", "faithfulness", overall["faithfulness"]),
        row("Answer Relevance (judge)", "answer_relevance", overall["answer_relevance"]),
        row("Citation Accuracy", "citation_accuracy", overall["citation_accuracy"]),
        row("Refusal Accuracy", "refusal_accuracy", overall["refusal_accuracy"]),
        row("Hallucination Rate (judge)", "hallucination_rate", overall["hallucination_rate"]),
        f"| p50 latency (generation) | {overall['p50_latency_ms']} ms | | |",
        row("p95 latency (generation)", "p95_latency_ms", overall["p95_latency_ms"]),
        f"| Avg cost/req | ${overall['avg_cost_usd']:.6f} | <= $0.005 | "
        f"{'ĐẠT' if overall['avg_cost_usd'] <= 0.005 else 'CHƯA ĐẠT'} |",
        f"| Error rate | {_fmt(overall['error_rate'])} | <= 0.01 | "
        f"{'ĐẠT' if overall['error_rate'] <= 0.01 else 'CHƯA ĐẠT'} |",
        f"| Fallback rate | {_fmt(overall['fallback_rate'])} | (theo dõi) | |",
        "| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |",
        "",
        *_fallback_note(results),
        "> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk "
        "runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, "
        "hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan "
        "thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi "
        "retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn "
        "không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là "
        "giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground "
        "truth thưa (citation-based), không phải lỗi retrieval. Context Recall "
        "và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.",
        "",
        "## Theo category",
        "",
        "| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | "
        "Answer Rel. | Hallucination | Ambiguity handled |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c in _category_breakdown(results):
        cret = c.get("retrieval", {})
        amb_col = (
            f"{_fmt(c['ambiguity_handling_rate'])} ({c['n_ambiguity_scored']})"
            if c["n_ambiguity_scored"]
            else "-"
        )
        lines.append(
            f"| {c['category']} | {c['n']} | {_fmt(cret.get('recall_at_k'))} | "
            f"{_fmt(c['refusal_accuracy'])} | {_fmt(c['citation_accuracy'])} | "
            f"{_fmt(c['faithfulness'])} | {_fmt(c['answer_relevance'])} | "
            f"{_fmt(c['hallucination_rate'])} | {amb_col} |"
        )
    lines += [
        "",
        "> **Ambiguity handled** (chỉ category `ambiguous`, requires_clarification=True): "
        "% câu trả lời hoặc hỏi lại người dùng để làm rõ, hoặc bao quát đủ các nhánh điều "
        "kiện thay vì chốt 1 nhánh duy nhất — đo bằng heuristic văn bản "
        "(`src/evaluation/metrics.py::ambiguity_handled`), không tốn thêm lệnh gọi judge. "
        "Hệ thống hiện KHÔNG có prompt/cơ chế hỏi lại làm rõ (xem "
        "src/promptops/templates.py) nên `refusal_accuracy` luôn 'đúng' một cách vô nghĩa "
        "cho category này (requires_refusal=False, hệ thống không refuse) — cột này là "
        "chỉ số thật duy nhất phản ánh có xử lý mơ hồ hợp lý hay không.",
    ]

    agreement = overall.get("inter_judge_agreement")
    if agreement:
        lines += [
            "",
            "## Inter-judge agreement",
            "",
            f"> Judge chính (`judge` tier, gemini-3-flash-preview) so với judge phụ "
            f"(`cheap` tier, gemini-3.1-flash-lite) trên cùng {agreement['n_pairs']} cặp "
            "(question, answer, context). Cả 2 đều là Gemini (chưa có key OpenAI/Anthropic — "
            "xem config/model_gateway.yaml) nên đây là so sánh giữa model MẠNH và model NHẸ "
            "cùng provider, không phải đa dạng provider thật; không có judge nào là ground "
            "truth tuyệt đối, agreement thấp không tự động nghĩa là 1 trong 2 sai.",
            "",
            "| Tiêu chí | Mean abs diff | Exact match rate |",
            "|---|---:|---:|",
        ]
        for crit in ("faithfulness", "answer_relevance", "context_relevance"):
            lines.append(
                f"| {crit} | {_fmt(agreement[f'{crit}_mean_abs_diff'])} | "
                f"{_fmt(agreement[f'{crit}_exact_match_rate'])} |"
            )
        lines.append(
            f"| hallucination (bool) | - | {_fmt(agreement['hallucination_agreement_rate'])} |"
        )

    failures = _failure_cases(results)
    lines += [
        "",
        f"## Failure cases ({len(failures)} câu, tối đa 30 hiển thị)",
        "",
        "| question_id | category | câu hỏi | lý do |",
        "|---|---|---|---|",
    ]
    if failures:
        for fl in failures:
            q_short = fl["question"][:80].replace("|", "/")
            lines.append(f"| {fl['question_id']} | {fl['category']} | {q_short} | {fl['reasons']} |")
    else:
        lines.append("| - | - | Không có câu nào trượt tiêu chí nào. | - |")

    doc_path = RESULTS_DOC_DIR / f"results_evaluation_{mode}.md"
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    return doc_path


def write_outputs(
    mode: str, results: list[QuestionResult], meta: dict[str, Any], eval_k: int = 5
) -> None:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    csv_path = write_csv(mode, results, ts)
    doc_path = write_markdown(mode, results, meta, ts, eval_k=eval_k)
    print(f"\nCSV -> {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"Report -> {doc_path.relative_to(PROJECT_ROOT)}")
