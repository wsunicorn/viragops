"""Unit tests for Prometheus metrics recording (Phase 10, Module 7) —
src/observability/metrics.py. Reads the real prometheus_client default
registry (module-level singletons) rather than mocking, since the whole
point is verifying record_request() actually updates them."""

from __future__ import annotations

from prometheus_client import REGISTRY

from src.observability import metrics as obs_metrics


def _counter_value(name: str, labels: dict[str, str] | None = None) -> float:
    return REGISTRY.get_sample_value(name, labels or {}) or 0.0


def test_record_request_increments_request_count():
    labels = {"prompt_version": "p_test_metrics_1", "refusal": "False"}
    trace = {"prompt_version": "p_test_metrics_1", "refusal": False}
    before = _counter_value("viragops_qa_requests_total", labels)
    obs_metrics.record_request(trace, total_latency_ms=1200)
    after = _counter_value("viragops_qa_requests_total", labels)
    assert after == before + 1


def test_record_request_tracks_tokens_and_cost():
    trace = {
        "prompt_version": "p_test_metrics_2", "refusal": False,
        "input_tokens": 100, "output_tokens": 50, "cost_usd": 0.001,
    }
    before_cost = _counter_value("viragops_cost_usd_total")
    obs_metrics.record_request(trace, total_latency_ms=1000)
    after_cost = _counter_value("viragops_cost_usd_total")
    assert after_cost >= before_cost + 0.001


def test_record_request_tracks_error_labels():
    trace = {"prompt_version": "p_test_metrics_3", "refusal": True, "error_labels": ["no_context"]}
    before = _counter_value("viragops_errors_total", {"label": "no_context"})
    obs_metrics.record_request(trace, total_latency_ms=500)
    after = _counter_value("viragops_errors_total", {"label": "no_context"})
    assert after == before + 1


def test_record_request_tracks_fallback_but_not_primary():
    trace_primary = {"prompt_version": "p_test_metrics_4", "refusal": False, "fallback_hop": "primary"}
    before = _counter_value("viragops_fallback_total", {"hop": "primary"})
    obs_metrics.record_request(trace_primary, total_latency_ms=500)
    after = _counter_value("viragops_fallback_total", {"hop": "primary"})
    assert after == before  # "primary" không tính là fallback

    trace_fallback = {"prompt_version": "p_test_metrics_4", "refusal": False, "fallback_hop": "secondary"}
    before2 = _counter_value("viragops_fallback_total", {"hop": "secondary"})
    obs_metrics.record_request(trace_fallback, total_latency_ms=500)
    after2 = _counter_value("viragops_fallback_total", {"hop": "secondary"})
    assert after2 == before2 + 1


def test_record_request_never_raises_on_minimal_trace():
    # Trace tối thiểu (thiếu hầu hết field) không được làm crash — quan
    # sát không được không chặn request.
    obs_metrics.record_request({}, total_latency_ms=0)


def test_record_request_never_raises_on_malformed_trace():
    obs_metrics.record_request({"error_labels": "not_a_list"}, total_latency_ms=-1)


def test_record_request_tracks_model_usage():
    trace = {
        "prompt_version": "p_test_metrics_5", "refusal": False,
        "model_provider": "litellm", "model_name": "gemini-3.1-flash-lite",
    }
    before = _counter_value(
        "viragops_model_usage_total", {"provider": "litellm", "model": "gemini-3.1-flash-lite"}
    )
    obs_metrics.record_request(trace, total_latency_ms=500)
    after = _counter_value(
        "viragops_model_usage_total", {"provider": "litellm", "model": "gemini-3.1-flash-lite"}
    )
    assert after == before + 1


def test_set_data_version_info_sets_gauge():
    obs_metrics.set_data_version_info("data_20260713")
    value = REGISTRY.get_sample_value("viragops_data_age_days")
    assert value is not None and value >= 0


def test_set_data_version_info_ignores_bad_format():
    obs_metrics.set_data_version_info("not_a_real_version")  # không raise
    obs_metrics.set_data_version_info(None)  # không raise
