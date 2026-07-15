"""Aggregate every structured eval-run summary JSON (data/eval/*_summary.json,
produced by scripts/run_evaluation.py's src.evaluation.report.write_summary_json
across Phases 8-12) into one machine-readable blob (Phase 12).

This does NOT write the prose synthesis — docs/system/experiments/
results_final_summary.md is hand-written for accuracy (a script blindly
concatenating markdown tables from 6+ differently-shaped reports would
either be too naive to be correct or too complex to trust more than
writing it directly). This script's job is narrower and safe to automate:
collect the already-real structured numbers into one indexed JSON so a
future dashboard/report generator has one place to read from instead of
globbing data/eval/ itself.

Usage: python scripts/generate_final_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

EVAL_DIR = PROJECT_ROOT / "data" / "eval"
OUT_PATH = EVAL_DIR / "final_report_data.json"


def main() -> None:
    runs = []
    for path in sorted(EVAL_DIR.glob("*_summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        runs.append({"file": path.name, **data})

    OUT_PATH.write_text(json.dumps({"n_runs": len(runs), "runs": runs}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"aggregated {len(runs)} eval-run summaries -> {OUT_PATH}")
    for r in runs:
        meta = r.get("meta", {})
        print(f"  {r['file']}: mode={r.get('mode')} prompt={meta.get('prompt_version')} n={r.get('n_questions')}")


if __name__ == "__main__":
    main()
