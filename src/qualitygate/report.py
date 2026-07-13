"""Quality Gate Markdown report writer (Phase 9, Module 6) — same
CSV/Markdown-not-a-dashboard-tool convention as src/evaluation/report.py
(Langfuse/PostgreSQL storage named in modules/06_quality_gate_cicd.md was
never wired up; Markdown is what's actually true here)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.qualitygate.gate import GateDecision

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DOC_DIR = PROJECT_ROOT / "docs" / "system" / "experiments"


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.4f}"


def write_markdown(
    decision: GateDecision,
    config: dict[str, Any],
    current_meta: dict[str, Any],
    baseline_meta: dict[str, Any] | None = None,
) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    lines = [
        f"# Quality Gate report — {ts} UTC",
        "",
        f"> gate_config_id=`{config.get('gate_config_id')}`, eval_run mode=`{current_meta.get('mode')}`"
        f" (`{current_meta.get('generated_at')}`)"
        + (
            f", baseline=`{baseline_meta.get('mode')}` (`{baseline_meta.get('generated_at')}`)"
            if baseline_meta
            else ", KHÔNG có baseline (chỉ so ngưỡng tuyệt đối, không check regression)"
        ),
        "",
        f"## Quyết định: **{decision.status}**",
        "",
    ]

    if decision.status == "BLOCK":
        lines.append("Có ít nhất 1 critical metric vi phạm hoặc regression vượt ngưỡng — giữ version cũ.")
    elif decision.status == "WARN":
        lines.append("Critical metric đều đạt, nhưng có warning metric vi phạm — cần reviewer xác nhận.")
    else:
        lines.append("Tất cả critical metric đạt, không warning nào vi phạm.")

    lines += ["", "## Critical metrics", "", "| Metric | Giá trị | Baseline | Vi phạm |", "|---|---:|---:|---|"]
    crit_names = list(config.get("critical_metrics", {}).keys())
    violated_names = {v.metric for v in decision.critical_violations}
    for name in crit_names:
        value = decision.metrics.get(name)
        baseline_value = (decision.baseline_metrics or {}).get(name)
        mark = "❌" if name in violated_names else "✅"
        lines.append(f"| {name} | {_fmt(value)} | {_fmt(baseline_value)} | {mark} |")

    lines += ["", "## Warning metrics", "", "| Metric | Giá trị | Baseline | Vi phạm |", "|---|---:|---:|---|"]
    warn_names = list(config.get("warning_metrics", {}).keys())
    warn_violated_names = {v.metric for v in decision.warning_violations}
    for name in warn_names:
        value = decision.metrics.get(name)
        baseline_value = (decision.baseline_metrics or {}).get(name)
        mark = "❌" if name in warn_violated_names else "✅"
        lines.append(f"| {name} | {_fmt(value)} | {_fmt(baseline_value)} | {mark} |")

    if decision.critical_violations or decision.warning_violations:
        lines += ["", "## Chi tiết vi phạm", ""]
        for v in decision.critical_violations:
            lines.append(f"- **[CRITICAL/{v.reason}]** {v.detail}")
        for v in decision.warning_violations:
            lines.append(f"- **[WARNING/{v.reason}]** {v.detail}")

    doc_path = RESULTS_DOC_DIR / f"results_quality_gate_{ts}.md"
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    return doc_path
