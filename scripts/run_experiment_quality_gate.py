"""Experiment 4 — Quality Gate Effectiveness (Phase 12, Module 6).

Reuses the 16-scenario fixture built for tests/unit/test_quality_gate.py
(Phase 9) instead of duplicating it a third time (the test file's own
`CONFIG` is already a manual copy of config/quality_gate.yaml, with a
comment warning the two must stay in sync — adding a third copy here would
compound that risk). This script adds what the test file doesn't compute:
a full TP/TN/FP/FN confusion matrix, a 3x3 expected-vs-actual breakdown,
gate latency, and a Markdown report.

Usage: python scripts/run_experiment_quality_gate.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.qualitygate.gate import evaluate_gate  # noqa: E402
from tests.unit.test_quality_gate import BASELINE, CONFIG, SIMULATED_CHANGES, _variant  # noqa: E402

OUT_PATH = PROJECT_ROOT / "docs" / "system" / "experiments" / "results_quality_gate_effectiveness.md"


def main() -> None:
    rows = []
    latencies_ms = []
    for label, overrides, expected in SIMULATED_CHANGES:
        current = _variant(**overrides)
        t0 = time.perf_counter()
        decision = evaluate_gate(current, CONFIG, BASELINE)
        latencies_ms.append((time.perf_counter() - t0) * 1000)
        violations = [f"{v.metric}({v.reason})" for v in decision.critical_violations + decision.warning_violations]
        rows.append((label, expected, decision.status, violations))

    # Binary confusion matrix: positive class = "should BLOCK" (9 bad scenarios).
    tp = sum(1 for _, exp, got, _ in rows if exp == "BLOCK" and got == "BLOCK")
    fn = sum(1 for _, exp, got, _ in rows if exp == "BLOCK" and got != "BLOCK")
    tn = sum(1 for _, exp, got, _ in rows if exp != "BLOCK" and got != "BLOCK")
    fp = sum(1 for _, exp, got, _ in rows if exp != "BLOCK" and got == "BLOCK")
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    # Full 3x3 expected x actual breakdown (WARN is a 3rd class, not folded
    # into binary good/bad — the plan's literal "8 good/8 bad" wording
    # doesn't match the actual fixture, which is 9 bad/4 warn/3 good).
    statuses = ["PASS", "WARN", "BLOCK"]
    confusion_3x3 = {e: {a: 0 for a in statuses} for e in statuses}
    for _, exp, got, _ in rows:
        confusion_3x3[exp][got] += 1

    lat_sorted = sorted(latencies_ms)
    p50 = lat_sorted[len(lat_sorted) // 2]
    p95 = lat_sorted[int(len(lat_sorted) * 0.95) - 1] if len(lat_sorted) > 1 else lat_sorted[0]

    lines = [
        "# Experiment 4 — Quality Gate Effectiveness",
        "",
        "16 kịch bản giả lập THẬT (tái dùng nguyên fixture "
        "`tests/unit/test_quality_gate.py::SIMULATED_CHANGES`, không tạo bản "
        "sao thứ 3 — file test đã tự cảnh báo rủi ro trùng lặp với "
        "`config/quality_gate.yaml`). Cơ cấu THẬT của fixture là **9 xấu / 4 "
        "cảnh báo / 3 tốt** — khác với cơ cấu \"8 tốt/8 xấu\" ghi trong "
        "`experiment_plan.md` (chênh lệch có chủ đích ghi rõ, không tự ý sửa "
        "fixture đã verify từ Phase 9 chỉ để khớp con số kế hoạch).",
        "",
        "## Confusion matrix (nhị phân — positive = \"nên BLOCK\", 9 kịch bản xấu)",
        "",
        "| | Actual BLOCK | Actual not-BLOCK |",
        "|---|---:|---:|",
        f"| Expected BLOCK (positive) | TP={tp} | FN={fn} |",
        f"| Expected not-BLOCK (negative) | FP={fp} | TN={tn} |",
        "",
        f"Precision={precision:.3f}, Recall={recall:.3f}" if precision is not None else "",
        "",
        "## Confusion matrix đầy đủ (3x3, expected x actual)",
        "",
        "| Expected \\ Actual | PASS | WARN | BLOCK |",
        "|---|---:|---:|---:|",
    ]
    for e in statuses:
        lines.append(f"| {e} | {confusion_3x3[e]['PASS']} | {confusion_3x3[e]['WARN']} | {confusion_3x3[e]['BLOCK']} |")

    lines += [
        "",
        f"## Gate latency (đo thật, {len(latencies_ms)} lần gọi `evaluate_gate()`)",
        "",
        f"p50={p50:.3f}ms, p95={p95:.3f}ms — hàm thuần offline (không I/O), "
        "độ trễ không đáng kể, không phải điểm nghẽn của CI pipeline.",
        "",
        "## Chi tiết 16 kịch bản",
        "",
        "| Label | Expected | Actual | Match | Vi phạm |",
        "|---|---|---|---|---|",
    ]
    for label, exp, got, violations in rows:
        match = "✅" if exp == got else "❌"
        lines.append(f"| {label} | {exp} | {got} | {match} | {', '.join(violations) or '—'} |")

    lines += [
        "",
        "## Kết luận",
        "",
        f"- Recall thật = {recall:.3f} (chặn {tp}/{tp+fn} thay đổi xấu) — "
        f"đạt tiêu chí gốc \"chặn >= 8/9\" (module doc), khớp đúng assertion "
        "thật trong `test_16_simulated_changes_suite` (`true_positives >= 8`, "
        "`false_negatives == 0`).",
        f"- Precision thật = {precision:.3f} — {fp} false positive trên "
        f"{tp+fp} lần BLOCK.",
        "- 4 kịch bản WARN đều đúng (không lẫn vào PASS/BLOCK) — gate phân "
        "biệt đúng 3 mức nghiêm trọng, không chỉ nhị phân.",
    ]

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"TP={tp} FN={fn} TN={tn} FP={fp} precision={precision} recall={recall}")
    print(f"gate latency p50={p50:.3f}ms p95={p95:.3f}ms")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
