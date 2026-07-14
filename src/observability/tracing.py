"""Langfuse tracing (Phase 10, Module 7).

Langfuse Cloud (free tier), NOT self-hosted — see CHECKLIST Phase 10 for
the decision (self-hosting needs 4 extra heavy containers: langfuse-web/
worker + ClickHouse + MinIO, on a dev machine that has already hit real
friction with heavy Docker stacks — see CHECKLIST Phase 1/3 CDN issues).

Every function here is BEST-EFFORT and fails open: a Langfuse outage,
missing credentials, or SDK bug must never break a QA request — tracing
is an observability concern, not a correctness guardrail (unlike the
citation fail-closed policy in src/rag/citation.py, which SHOULD block).
All exceptions are caught and logged; callers always get back a value
(possibly None) they can pass straight through the rest of the pipeline
without checking for a Langfuse-specific failure mode.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from langfuse import Langfuse
except ImportError:  # optional dependency group "observability" not installed
    Langfuse = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


def make_langfuse_client(host: str, public_key: str, secret_key: str) -> Any | None:
    """None when the SDK isn't installed or credentials are blank — the
    caller (RagService) treats None as "tracing disabled" everywhere."""
    if Langfuse is None or not public_key or not secret_key:
        return None
    try:
        return Langfuse(host=host, public_key=public_key, secret_key=secret_key)
    except Exception:
        logger.exception("Langfuse client init failed — tracing disabled, request vẫn tiếp tục")
        return None


def start_qa_span(langfuse: Any | None, trace_id: str, question: str) -> Any | None:
    if langfuse is None:
        return None
    try:
        # seed=trace_id -> Langfuse's 32-hex trace_id is deterministic from
        # our own trace_<ts>_<hash> id, so the 2 systems correlate without
        # storing a mapping anywhere.
        lf_trace_id = Langfuse.create_trace_id(seed=trace_id)
        return langfuse.start_span(
            name="qa_answer",
            trace_context={"trace_id": lf_trace_id},
            input={"question": question},
        )
    except Exception:
        logger.exception("Langfuse start_span failed — bỏ qua trace này")
        return None


def start_generation_span(lf_span: Any | None, prompt: str, tier: str) -> Any | None:
    if lf_span is None:
        return None
    try:
        return lf_span.start_generation(name="llm_generate", input=prompt, model=tier)
    except Exception:
        logger.exception("Langfuse start_generation failed")
        return None


def end_generation_span(lf_gen: Any | None, gen_result: Any, cost_usd: float) -> None:
    if lf_gen is None:
        return
    try:
        lf_gen.update(
            output=gen_result.text,
            model=gen_result.model,
            usage_details={"input": gen_result.input_tokens, "output": gen_result.output_tokens},
            cost_details={"total": cost_usd},
        )
        lf_gen.end()
    except Exception:
        logger.exception("Langfuse end_generation failed")


def end_qa_span(lf_span: Any | None, trace: dict, confidence: float | None) -> None:
    """metadata mirrors modules/07_observability_cost.md's "Trace fields
    bắt buộc" list — every field named there that RagService already
    computes gets sent here, nothing invented for Langfuse specifically."""
    if lf_span is None:
        return
    try:
        output = {"answer": trace.get("answer"), "refusal": trace.get("refusal")}
        lf_span.update_trace(
            session_id=trace.get("session_id"),
            input={"question": trace.get("question")},
            output=output,
            metadata={
                "trace_id": trace.get("trace_id"),
                "request_id": trace.get("request_id"),
                "normalized_query": trace.get("normalized_query"),
                "prompt_version": trace.get("prompt_version"),
                "data_version": trace.get("data_version"),
                "index_version": trace.get("index_version"),
                "retrieval_config_id": trace.get("retrieval_config_id"),
                "model_provider": trace.get("model_provider"),
                "model_name": trace.get("model_name"),
                "fallback_hop": trace.get("fallback_hop"),
                "error_labels": trace.get("error_labels"),
                "confidence": confidence,
                "retrieved_chunk_ids": [c["chunk_id"] for c in trace.get("retrieved") or []],
                "input_tokens": trace.get("input_tokens"),
                "output_tokens": trace.get("output_tokens"),
                "cost_usd": trace.get("cost_usd"),
            },
            tags=[t for t in (trace.get("prompt_version"), trace.get("data_version")) if t],
        )
        lf_span.update(output=output)
        lf_span.end()
    except Exception:
        logger.exception("Langfuse end_qa_span failed")


def flush(langfuse: Any | None) -> None:
    """Langfuse batches+sends async in a background thread — a long-lived
    API server doesn't need this, but short-lived scripts (eval runs,
    demo traffic generator) must call it before exiting or the last
    batch never reaches Langfuse Cloud."""
    if langfuse is not None:
        try:
            langfuse.flush()
        except Exception:
            logger.exception("Langfuse flush failed")
