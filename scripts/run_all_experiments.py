"""Experiment index/orchestrator (Phase 12) — the "Kiểm tra dự kiến" command
the checklist names. Defaults to a STATUS report only, not a blind rerun:
running all 6 experiments live costs real Gemini quota across dozens of
calls each (this project has repeatedly hit daily quota limits doing
exactly that — see CHECKLIST Phase 4/8) and takes tens of minutes per
experiment. The checked-in reports in docs/system/experiments/ are the
canonical last real run of each; use --rerun to redo a specific one
explicitly when you actually want to spend the quota.

Usage:
    python scripts/run_all_experiments.py              # status only
    python scripts/run_all_experiments.py --rerun exp4  # re-run just Exp 4
    python scripts/run_all_experiments.py --rerun all   # re-run everything (expensive!)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = PROJECT_ROOT / "docs" / "system" / "experiments"

# (id, description, script, result file to check for)
EXPERIMENTS = [
    ("exp1", "Chunking Ablation", "scripts/run_experiment.py --experiment chunking_ablation",
     "results_chunking_ablation.md"),
    ("exp2", "Retrieval + Reranking", "scripts/run_experiment.py --experiment retrieval_reranking",
     "results_retrieval_reranking.md"),
    ("exp3", "Model/Provider Comparison", "scripts/run_experiment_model_provider.py",
     "results_model_provider_comparison.md"),
    ("exp4", "Quality Gate Effectiveness", "scripts/run_experiment_quality_gate.py",
     "results_quality_gate_effectiveness.md"),
    ("exp5", "Observability + Error Classification", "scripts/run_experiment_error_classification.py",
     "results_error_classification.md"),
    ("exp6", "Optimization O1-O8", "scripts/run_experiment_optimization.py",
     "results_optimization_o1_o8.md"),
]


def _status(filename: str) -> str:
    path = EXP_DIR / filename
    if not path.exists():
        return "MISSING"
    age = datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return f"exists, {age.days}d {age.seconds // 3600}h old"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rerun", default=None, help="'all' or a specific experiment id (exp1..exp6)")
    args = parser.parse_args()

    print(f"{'id':<6} {'name':<38} {'status':<24} command")
    print("-" * 110)
    for exp_id, name, cmd, result_file in EXPERIMENTS:
        print(f"{exp_id:<6} {name:<38} {_status(result_file):<24} python {cmd}")

    if args.rerun is None:
        print("\n(status only — pass --rerun <exp_id|all> to actually execute; each real run costs Gemini quota)")
        return

    targets = EXPERIMENTS if args.rerun == "all" else [e for e in EXPERIMENTS if e[0] == args.rerun]
    if not targets:
        raise SystemExit(f"unknown experiment id: {args.rerun!r}")

    for exp_id, name, cmd, _ in targets:
        print(f"\n=== re-running {exp_id} ({name}) ===")
        result = subprocess.run([sys.executable, *cmd.split()], cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"{exp_id} FAILED (exit {result.returncode}) — stopping")
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
