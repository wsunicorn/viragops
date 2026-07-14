"""Unit tests for Langfuse tracing wrapper (Phase 10, Module 7) —
src/observability/tracing.py. Every function must fail open: a broken/
missing Langfuse client must return None or no-op, never raise, since
observability must never break a QA request (see module docstring)."""

from __future__ import annotations

from src.observability import tracing as obs_tracing


class _FakeGeneration:
    def __init__(self):
        self.ended = False
        self.updated_with: dict | None = None

    def update(self, **kwargs):
        self.updated_with = kwargs

    def end(self):
        self.ended = True


class _FakeSpan:
    def __init__(self, raise_on_generation: bool = False, raise_on_update_trace: bool = False):
        self.ended = False
        self.updated_with: dict | None = None
        self.trace_updated_with: dict | None = None
        self._raise_on_generation = raise_on_generation
        self._raise_on_update_trace = raise_on_update_trace

    def start_generation(self, **kwargs):
        if self._raise_on_generation:
            raise RuntimeError("simulated Langfuse failure")
        return _FakeGeneration()

    def update_trace(self, **kwargs):
        if self._raise_on_update_trace:
            raise RuntimeError("simulated Langfuse failure")
        self.trace_updated_with = kwargs

    def update(self, **kwargs):
        self.updated_with = kwargs

    def end(self):
        self.ended = True


class _FakeLangfuseClient:
    def __init__(self, span: _FakeSpan | None = None, raise_on_start_span: bool = False):
        self._span = span or _FakeSpan()
        self._raise_on_start_span = raise_on_start_span
        self.flushed = False

    def start_span(self, **kwargs):
        if self._raise_on_start_span:
            raise RuntimeError("simulated Langfuse failure")
        return self._span

    def flush(self):
        self.flushed = True


class _FakeGenResult:
    text = "câu trả lời mô phỏng"
    model = "gemini-3.1-flash-lite"
    input_tokens = 100
    output_tokens = 50


# --- make_langfuse_client -------------------------------------------------


def test_make_langfuse_client_none_when_credentials_blank():
    assert obs_tracing.make_langfuse_client("https://cloud.langfuse.com", "", "") is None


def test_make_langfuse_client_none_when_only_public_key_set():
    assert obs_tracing.make_langfuse_client("https://cloud.langfuse.com", "pk-x", "") is None


# --- start_qa_span / end_qa_span ------------------------------------------


def test_start_qa_span_none_when_client_none():
    assert obs_tracing.start_qa_span(None, "trace_1", "câu hỏi") is None


def test_start_qa_span_returns_span_from_client():
    client = _FakeLangfuseClient()
    span = obs_tracing.start_qa_span(client, "trace_1", "câu hỏi")
    assert span is client._span


def test_start_qa_span_fails_open_on_client_error():
    client = _FakeLangfuseClient(raise_on_start_span=True)
    assert obs_tracing.start_qa_span(client, "trace_1", "câu hỏi") is None


def test_end_qa_span_none_span_is_noop():
    obs_tracing.end_qa_span(None, {"trace_id": "t1"}, confidence=0.8)  # không raise


def test_end_qa_span_updates_trace_and_ends_span():
    span = _FakeSpan()
    trace = {
        "trace_id": "trace_1", "request_id": "req_1", "session_id": None,
        "question": "câu hỏi", "answer": "trả lời", "refusal": False,
        "prompt_version": "p7_citation_complete_safe_v1", "data_version": "data_20260713",
        "retrieved": [{"chunk_id": "chunk_a", "score": 1.5}],
        "error_labels": [],
    }
    obs_tracing.end_qa_span(span, trace, confidence=0.75)
    assert span.ended is True
    assert span.trace_updated_with["metadata"]["confidence"] == 0.75
    assert span.trace_updated_with["metadata"]["retrieved_chunk_ids"] == ["chunk_a"]
    assert "p7_citation_complete_safe_v1" in span.trace_updated_with["tags"]


def test_end_qa_span_fails_open_on_error():
    span = _FakeSpan(raise_on_update_trace=True)
    obs_tracing.end_qa_span(span, {"trace_id": "t1"}, confidence=None)  # không raise


# --- start_generation_span / end_generation_span --------------------------


def test_start_generation_span_none_when_lf_span_none():
    assert obs_tracing.start_generation_span(None, "prompt", "balanced") is None


def test_start_generation_span_returns_generation_from_span():
    span = _FakeSpan()
    gen = obs_tracing.start_generation_span(span, "prompt text", "balanced")
    assert isinstance(gen, _FakeGeneration)


def test_start_generation_span_fails_open_on_error():
    span = _FakeSpan(raise_on_generation=True)
    assert obs_tracing.start_generation_span(span, "prompt", "balanced") is None


def test_end_generation_span_none_is_noop():
    obs_tracing.end_generation_span(None, _FakeGenResult(), cost_usd=0.001)  # không raise


def test_end_generation_span_updates_and_ends():
    gen = _FakeGeneration()
    obs_tracing.end_generation_span(gen, _FakeGenResult(), cost_usd=0.001)
    assert gen.ended is True
    assert gen.updated_with["output"] == "câu trả lời mô phỏng"
    assert gen.updated_with["usage_details"] == {"input": 100, "output": 50}
    assert gen.updated_with["cost_details"] == {"total": 0.001}


# --- flush -----------------------------------------------------------------


def test_flush_none_is_noop():
    obs_tracing.flush(None)  # không raise


def test_flush_calls_client_flush():
    client = _FakeLangfuseClient()
    obs_tracing.flush(client)
    assert client.flushed is True
