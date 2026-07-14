"""Seed real feedback from a completed full evaluation run (Phase 11,
Module 9) — "eval failures" is an explicit valid Input in the module doc's
Input/Output table, so this is not fabricated data, it's a real, already-
verified-live evaluation run reinterpreted as feedback.

Source: data/eval/eval_full_20260712_0938.csv (298 questions,
p1_grounded_v1, data_20260712) — chosen over the OTHER full-run CSV that
exists (eval_full_20260712_1339.csv) after checking both directly: the
1339 run has 293/298 rows served by the tertiary (Ollama) fallback hop
(quota exhausted that day), including 100% of its multi_hop/ambiguous
rows — using it would misattribute Ollama's citation weaknesses to the
prompt. The 0938 run is 263/298 primary-hop (clean), 45/48 of its
multi_hop/ambiguous rows are primary — real citation-accuracy failures
from an actual generation call, not fallback noise. It predates p6/p7
(ran under p1_grounded_v1), but this is exactly the real data that
historically motivated building p6/p7's citation-completeness rule
(CHECKLIST "Sửa citation accuracy multi-hop/ambiguous") — and per the
2026-07-14 smoke re-test, p7 still hasn't fully closed this gap
(citation_accuracy=0.838, still below the 0.85 target, weakest in
multi_hop) — so treating this as a still-open cluster is honest, not
stale.

Each surviving row is joined to a REAL trace_id via
data/traces/traces.jsonl: exact question-text match + matching
data_version/prompt_version, taking the EARLIEST such trace (a question's
wording under a fixed prompt is static, so any real trace with that exact
signature is a genuine occurrence of the same failure — this avoids
having to reconstruct the precise start/end timestamps of one run among
several that shared prompt_version=p1_grounded_v1 that day, a needlessly
fragile alternative). Rows with no matching trace at all are skipped and
counted, not guessed — same fail-closed spirit as the earlier
relevant_chunks linking work (CHECKLIST Phase 4).

Usage: python scripts/seed_feedback_from_eval.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.feedback.classifier import classify_error_label  # noqa: E402
from src.feedback.store import FeedbackStore  # noqa: E402
from src.rag.trace_store import new_id  # noqa: E402

EVAL_CSV = PROJECT_ROOT / "data" / "eval" / "eval_full_20260712_0938.csv"
GOLDEN_SET = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
TRACES_JSONL = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"

REPORT_DATA_VERSION = "data_20260712"
REPORT_PROMPT_VERSION = "p1_grounded_v1"

TARGET_CATEGORIES = {"multi_hop", "ambiguous"}


def _load_golden_set() -> dict[str, dict]:
    items = {}
    with GOLDEN_SET.open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            items[item["id"]] = item
    return items


def _load_traces_by_question() -> dict[str, dict]:
    """question text -> earliest trace dict matching this run's
    data_version/prompt_version."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="chỉ in số liệu, không ghi Postgres")
    args = parser.parse_args()

    golden = _load_golden_set()
    by_question = _load_traces_by_question()

    matched, skipped_no_trace, skipped_not_target = 0, 0, 0
    store = None if args.dry_run else FeedbackStore(get_settings().postgres_dsn)
    created_ids: list[str] = []

    with EVAL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"]

            if category not in TARGET_CATEGORIES or not row["citation_accuracy"]:
                # citation_accuracy rỗng = câu refusal, không có citation để
                # chấm — không phải lỗi citation, bỏ qua.
                skipped_not_target += 1
                continue
            citation_accuracy = float(row["citation_accuracy"])
            if citation_accuracy >= 1.0 or row["fallback_hop"] != "primary":
                skipped_not_target += 1
                continue

            golden_item = golden.get(row["question_id"])
            if golden_item is None:
                skipped_no_trace += 1
                continue
            trace = by_question.get(golden_item["question"])
            if trace is None:
                skipped_no_trace += 1
                continue

            error_label = classify_error_label(trace, "missing_citation")
            comment = (
                f"citation_accuracy={citation_accuracy:.2f} (eval full p1_grounded_v1, 2026-07-12, "
                f"clean primary-hop) — real signal that motivated p6/p7's citation-completeness rule."
            )
            matched += 1
            if store is not None:
                record = store.create(
                    feedback_id=new_id("fb"),
                    trace_id=trace["trace_id"],
                    feedback_type="missing_citation",
                    error_label=error_label,
                    comment=comment,
                    category=category,
                    source="eval_seed",
                )
                created_ids.append(record.feedback_id)

    print(f"matched (feedback created): {matched}")
    print(f"skipped, not in target filter (category/citation_accuracy/non-primary-hop): {skipped_not_target}")
    print(f"skipped, no matching trace: {skipped_no_trace}")
    if args.dry_run:
        print("(--dry-run: không ghi Postgres)")
    else:
        print(f"feedback_ids: {created_ids}")


if __name__ == "__main__":
    main()
