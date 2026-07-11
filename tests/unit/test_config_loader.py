"""Unit tests for versioned config loading."""

import pytest

from src.common.config_loader import ConfigError, active_config_ids, load_config


def test_all_sample_configs_load_with_ids():
    ids = active_config_ids()
    assert ids["retrieval.yaml"] == "hybrid_dbsf_v2"
    assert ids["prompts.yaml"] == "rag_qa_vi"
    assert ids["model_gateway.yaml"] == "gateway_gemini_free_v1"
    assert ids["quality_gate.yaml"] == "gate_default_v1"
    assert ids["ingest.yaml"] == "ingest_iuh_v1"
    assert "missing" not in ids.values()


def test_quality_gate_thresholds_match_metric_contract():
    """Ngưỡng trong config phải khớp contracts/metric_definitions.md."""
    gate = load_config("quality_gate.yaml")
    critical = gate["critical_metrics"]
    assert critical["recall_at_5"]["min"] == 0.85
    assert critical["faithfulness"]["min"] == 0.85
    assert critical["hallucination_rate"]["max"] == 0.05
    assert critical["refusal_accuracy"]["min"] == 0.90
    assert gate["regression"]["max_quality_drop"] == 0.03


def test_missing_config_raises():
    with pytest.raises(ConfigError):
        load_config("does_not_exist.yaml")
