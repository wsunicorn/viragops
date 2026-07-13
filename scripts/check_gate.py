"""Quality Gate CLI (Phase 9, Module 6).

Reads 2 aggregate summary JSONs already produced by
scripts/run_evaluation.py (src/evaluation/report.py::write_summary_json)
and decides PASS/WARN/BLOCK per config/quality_gate.yaml. Does NOT run any
evaluation itself — run scripts/run_evaluation.py first.

Usage:
    python scripts/check_gate.py --eval-run data/eval/eval_smoke_20260713_0517_summary.json
    python scripts/check_gate.py --eval-run <path> --baseline <path>
    python scripts/check_gate.py --mode smoke --latest    # auto-pick newest smoke summary

Exit code: 0 for PASS/WARN, 1 for BLOCK — a CI step can gate on this
directly (`run: python scripts/check_gate.py ... `) without extra parsing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.qualitygate.gate import evaluate_gate  # noqa: E402
from src.qualitygate.report import write_markdown  # noqa: E402

EVAL_DIR = PROJECT_ROOT / "data" / "eval"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "quality_gate.yaml"


def _latest_summary(mode: str) -> Path:
    candidates = sorted(EVAL_DIR.glob(f"eval_{mode}_*_summary.json"))
    if not candidates:
        raise SystemExit(f"No summary JSON found for mode={mode!r} in {EVAL_DIR}")
    return candidates[-1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)  # path ngoài repo (vd file tạm) -> in đường dẫn tuyệt đối thay vì crash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eval-run", help="đường dẫn summary JSON của eval run cần chấm")
    parser.add_argument("--baseline", help="đường dẫn summary JSON của baseline (optional)")
    parser.add_argument("--mode", choices=["smoke", "full", "targeted"], help="dùng với --latest")
    parser.add_argument("--latest", action="store_true", help="tự chọn summary JSON mới nhất theo --mode")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args = parser.parse_args()

    if args.latest:
        if not args.mode:
            raise SystemExit("--latest cần --mode")
        eval_run_path = _latest_summary(args.mode)
    elif args.eval_run:
        eval_run_path = Path(args.eval_run)
    else:
        raise SystemExit("Cần --eval-run <path> hoặc --mode <mode> --latest")

    current = _load(eval_run_path)
    baseline = _load(Path(args.baseline)) if args.baseline else None
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    decision = evaluate_gate(current, config, baseline)

    print(f"Eval run: {_display_path(eval_run_path)}")
    if args.baseline:
        print(f"Baseline: {_display_path(Path(args.baseline))}")
    print(f"Decision: {decision.status}")
    for v in decision.critical_violations:
        print(f"  [CRITICAL/{v.reason}] {v.detail}")
    for v in decision.warning_violations:
        print(f"  [WARNING/{v.reason}] {v.detail}")

    doc_path = write_markdown(decision, config, current, baseline)
    print(f"\nReport -> {_display_path(doc_path)}")

    return 1 if decision.status == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
