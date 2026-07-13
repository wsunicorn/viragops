"""Quality Gate decision logic (Phase 9, Module 6).

Turns an Evaluation Engine aggregate (src/evaluation/runner.py::aggregate(),
persisted as JSON by src/evaluation/report.py::write_summary_json()) into an
operational PASS/WARN/BLOCK decision per modules/06_quality_gate_cicd.md.

Deliberately takes a plain aggregate dict rather than importing
src.evaluation.runner.QuestionResult — the gate is a pure decision function
over numbers a report already produced; it must not re-run or re-derive
evaluation, only judge it. This also means the gate module never touches
Qdrant/Postgres/LiteLLM and can run (and be tested) with zero services.

Decision policy:
    BLOCK  if any critical metric fails its absolute min/max threshold, OR
           (when a baseline is given) any critical metric regressed more
           than `regression.max_quality_drop` from the baseline value.
    WARN   if no BLOCK but any warning metric fails its threshold.
    PASS   otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MetricKind = Literal["min", "max"]


@dataclass
class Violation:
    metric: str
    reason: str  # "threshold" | "regression" | "missing"
    detail: str


@dataclass
class GateDecision:
    status: Literal["PASS", "WARN", "BLOCK"]
    critical_violations: list[Violation] = field(default_factory=list)
    warning_violations: list[Violation] = field(default_factory=list)
    metrics: dict[str, float | None] = field(default_factory=dict)
    baseline_metrics: dict[str, float | None] | None = None


def _get_metric(aggregate: dict[str, Any], name: str) -> float | None:
    """Map a gate metric name to its value in a runner.aggregate() dict.

    A handful of gate metric names don't exist verbatim in the aggregate
    (different unit, nested under "retrieval") — everything else is a
    direct passthrough so new metrics don't need a new branch here.
    """
    if name == "recall_at_5":
        return aggregate.get("retrieval", {}).get("recall_at_k")
    if name == "p95_latency_seconds":
        ms = aggregate.get("p95_latency_ms")
        return ms / 1000.0 if ms is not None else None
    if name == "cost_per_request_usd":
        return aggregate.get("avg_cost_usd")
    return aggregate.get(name)


def _threshold_violation(name: str, value: float | None, bounds: dict[str, float]) -> Violation | None:
    if value is None:
        return Violation(name, "missing", f"{name}: không có giá trị trong aggregate (fail-closed)")
    if "min" in bounds and value < bounds["min"]:
        return Violation(name, "threshold", f"{name}={value:.4f} < min {bounds['min']}")
    if "max" in bounds and value > bounds["max"]:
        return Violation(name, "threshold", f"{name}={value:.4f} > max {bounds['max']}")
    return None


def _regression_violation(
    name: str, value: float, baseline_value: float | None, bounds: dict[str, float], max_drop: float
) -> Violation | None:
    if baseline_value is None:
        return None
    is_min_metric = "min" in bounds  # higher-is-better; "max" bounds are lower-is-better
    drop = (baseline_value - value) if is_min_metric else (value - baseline_value)
    if drop > max_drop:
        direction = "giảm" if is_min_metric else "tăng"
        return Violation(
            name, "regression",
            f"{name} {direction} {drop:.4f} so baseline ({baseline_value:.4f} -> {value:.4f}), "
            f"vượt max_quality_drop={max_drop}",
        )
    return None


def evaluate_gate(
    current: dict[str, Any],
    config: dict[str, Any],
    baseline: dict[str, Any] | None = None,
) -> GateDecision:
    critical_cfg: dict[str, dict[str, float]] = config.get("critical_metrics", {})
    warning_cfg: dict[str, dict[str, float]] = config.get("warning_metrics", {})
    max_drop = config.get("regression", {}).get("max_quality_drop", 0.0)

    metrics: dict[str, float | None] = {}
    baseline_metrics: dict[str, float | None] | None = {} if baseline is not None else None

    critical_violations: list[Violation] = []
    for name, bounds in critical_cfg.items():
        value = _get_metric(current, name)
        metrics[name] = value
        v = _threshold_violation(name, value, bounds)
        if v is not None:
            critical_violations.append(v)
            continue  # đã fail tuyệt đối, không cần check regression thêm

        if baseline is not None:
            baseline_value = _get_metric(baseline, name)
            baseline_metrics[name] = baseline_value  # type: ignore[index]
            if value is not None:
                rv = _regression_violation(name, value, baseline_value, bounds, max_drop)
                if rv is not None:
                    critical_violations.append(rv)

    warning_violations: list[Violation] = []
    for name, bounds in warning_cfg.items():
        value = _get_metric(current, name)
        metrics[name] = value
        v = _threshold_violation(name, value, bounds)
        if v is not None:
            warning_violations.append(v)
        if baseline is not None and baseline_metrics is not None:
            baseline_metrics[name] = _get_metric(baseline, name)

    if critical_violations:
        status: Literal["PASS", "WARN", "BLOCK"] = "BLOCK"
    elif warning_violations:
        status = "WARN"
    else:
        status = "PASS"

    return GateDecision(
        status=status,
        critical_violations=critical_violations,
        warning_violations=warning_violations,
        metrics=metrics,
        baseline_metrics=baseline_metrics,
    )
