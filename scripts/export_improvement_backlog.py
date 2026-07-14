"""Export the improvement backlog Markdown from real feedback clusters
(Phase 11, Module 9 task "Implement improvement backlog export").

Usage: python scripts/export_improvement_backlog.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.feedback.backlog import export_backlog  # noqa: E402
from src.feedback.clustering import cluster_feedback  # noqa: E402
from src.feedback.store import FeedbackStore  # noqa: E402

OUT_DIR = PROJECT_ROOT / "docs" / "system" / "experiments"
TRACES_JSONL = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"


def _load_questions_by_trace_id(trace_ids: set[str]) -> dict[str, str]:
    questions: dict[str, str] = {}
    with TRACES_JSONL.open(encoding="utf-8") as f:
        for line in f:
            trace = json.loads(line)
            if trace.get("trace_id") in trace_ids:
                questions[trace["trace_id"]] = trace["question"]
    return questions


def main() -> None:
    store = FeedbackStore(get_settings().postgres_dsn)
    items = store.list_all()
    trace_ids = {r.trace_id for r in items}
    questions_by_trace = _load_questions_by_trace_id(trace_ids)
    questions_by_trace_id = {r.trace_id: questions_by_trace[r.trace_id] for r in items if r.trace_id in questions_by_trace}

    clusters = cluster_feedback(items, questions=questions_by_trace_id)
    markdown = export_backlog(clusters)

    out_path = OUT_DIR / f"results_improvement_backlog_{datetime.now(UTC).strftime('%Y%m%d_%H%M')}.md"
    out_path.write_text(markdown, encoding="utf-8")
    print(f"wrote {out_path} ({len(items)} feedback, {len(clusters)} cluster)")


if __name__ == "__main__":
    main()
