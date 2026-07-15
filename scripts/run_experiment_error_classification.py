"""Experiment 5 — Observability + Error Classification (Phase 12, Module 7).

Applies src/feedback/classifier.py (built in Phase 11, never fed real
production feedback needed to run — it only reads trace fields) to every
real failure in the clean full-eval run (eval_full_20260712_0938.csv, 298
questions, p1_grounded_v1, mostly primary-hop — see
scripts/seed_feedback_from_eval.py's docstring for why this is the cleanest
full-scale real run available). Unlike that Phase 11 script, this one does
NOT filter to citation-only/primary-only — Exp5 wants the full realistic
error landscape, fallback-served rows included (those should classify as
provider_error).

Writes a random self-review sample (fixed seed) to a JSON file — the actual
review (reading each trace/answer and judging independently) happens by
hand afterward, same "AI self-review, not domain-expert" honesty already
used for golden-set review (Phase 2).

Usage: python scripts/run_experiment_error_classification.py
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feedback.classifier import classify_error_label  # noqa: E402

EVAL_CSV = PROJECT_ROOT / "data" / "eval" / "eval_full_20260712_0938.csv"
GOLDEN_SET = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
TRACES_JSONL = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"
OUT_MD = PROJECT_ROOT / "docs" / "system" / "experiments" / "results_error_classification.md"
SAMPLE_JSON = PROJECT_ROOT / "data" / "eval" / "error_classification_review_sample.json"

REPORT_DATA_VERSION = "data_20260712"
REPORT_PROMPT_VERSION = "p1_grounded_v1"
SAMPLE_SIZE = 25
SAMPLE_SEED = 12


def _load_golden_set() -> dict[str, dict]:
    items = {}
    with GOLDEN_SET.open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            items[item["id"]] = item
    return items


def _load_traces_by_question() -> dict[str, dict]:
    earliest: dict[str, dict] = {}
    with TRACES_JSONL.open(encoding="utf-8") as f:
        for line in f:
            trace = json.loads(line)
            if (
                trace.get("data_version") != REPORT_DATA_VERSION
                or trace.get("prompt_version") != REPORT_PROMPT_VERSION
            ):
                continue
            q = trace["question"]
            if q not in earliest or trace["created_at"] < earliest[q]["created_at"]:
                earliest[q] = trace
    return earliest


def _is_failure(row: dict) -> bool:
    if row["citation_accuracy"] and float(row["citation_accuracy"]) < 1.0:
        return True
    if row["hallucination"] == "True":
        return True
    if row["refusal_correct"] == "False":
        return True
    if row["hit_at_k"] and float(row["hit_at_k"]) == 0.0:
        return True
    return False


def main() -> None:
    golden = _load_golden_set()
    by_question = _load_traces_by_question()

    matched, skipped_no_trace, not_failure = 0, 0, 0
    classified: list[dict] = []

    with EVAL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not _is_failure(row):
                not_failure += 1
                continue
            golden_item = golden.get(row["question_id"])
            if golden_item is None:
                skipped_no_trace += 1
                continue
            trace = by_question.get(golden_item["question"])
            if trace is None:
                skipped_no_trace += 1
                continue

            label = classify_error_label(trace, "wrong_answer")
            matched += 1
            classified.append({
                "question_id": row["question_id"],
                "category": row["category"],
                "trace_id": trace["trace_id"],
                "question": golden_item["question"],
                "answer": trace.get("answer", ""),
                "citation_accuracy": row["citation_accuracy"],
                "hallucination": row["hallucination"],
                "refusal_correct": row["refusal_correct"],
                "fallback_hop": trace.get("fallback_hop"),
                "error_labels_trace": trace.get("error_labels") or [],
                "auto_label": label,
            })

    distribution = Counter(c["auto_label"] for c in classified)

    rng = random.Random(SAMPLE_SEED)
    sample = rng.sample(classified, min(SAMPLE_SIZE, len(classified)))
    SAMPLE_JSON.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Experiment 5 — Observability + Error Classification",
        "",
        f"Nguồn: `{EVAL_CSV.name}` (298 câu, `{REPORT_PROMPT_VERSION}`, "
        f"`{REPORT_DATA_VERSION}` — cùng file dùng seed feedback Phase 11, "
        "nhưng KHÔNG lọc citation-only/primary-only lần này — muốn thấy đúng "
        "bức tranh lỗi thật, kể cả provider_error từ câu bị fallback).",
        "",
        f"- Tổng câu: 298. Không phải lỗi (qua mọi 4 tiêu chí): {not_failure}.",
        f"- Câu lỗi match được trace: {matched}. Không match được trace: {skipped_no_trace}.",
        "",
        "## Phân bố nhãn lỗi tự động (rule-based, src/feedback/classifier.py)",
        "",
        "| error_label | Số câu | Tỷ lệ |",
        "|---|---:|---:|",
    ]
    for label, count in distribution.most_common():
        lines.append(f"| {label or '(none)'} | {count} | {count/matched:.1%} |")

    lines += [
        "",
        f"## Human-review sample (n={len(sample)}, seed={SAMPLE_SEED})",
        "",
        f"Mẫu random đã ghi ra `{SAMPLE_JSON.relative_to(PROJECT_ROOT)}` — phần review "
        "thật (đọc từng trace/answer, tự đánh giá nhãn ĐÚNG theo phán đoán độc lập, "
        "so với nhãn tự động) được làm thủ công và ghi tiếp vào bảng dưới đây "
        "(script chỉ tạo mẫu, KHÔNG tự chấm accuracy — tránh classifier tự chấm chính nó).",
        "",
        "*(bảng self-review điền tay bên dưới)*",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"matched={matched} skipped_no_trace={skipped_no_trace} not_failure={not_failure}")
    print("distribution:", dict(distribution))
    print(f"wrote {OUT_MD}")
    print(f"wrote {SAMPLE_JSON}")


if __name__ == "__main__":
    main()
