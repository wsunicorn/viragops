"""Integration test cho QA flow (Phase 5) — Qdrant THẬT + gateway MOCK.

Chạy được khi docker compose up (qdrant) và đã ingest (Phase 3). Tự skip
khi Qdrant/collection chưa sẵn sàng — không fail CI nơi không có service.
Gateway mock + embed_fn giả để không tốn quota Gemini: phần được test
thật ở đây là retrieval trên index thật, citation validation, refusal
pre-check, trace store và shape của response.
"""

from __future__ import annotations

import httpx
import pytest

from src.promptops.templates import SEED_PROMPTS
from src.rag.gateway_client import MockGateway
from src.rag.prompt_builder import StaticPromptProvider
from src.rag.schemas import QARequest
from src.rag.service import RagService

QDRANT_URL = "http://localhost:6333"


def _qdrant_ready() -> bool:
    try:
        return httpx.get(f"{QDRANT_URL}/collections", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _qdrant_ready(), reason="Qdrant not running")

# Template thật của p1 từ seed source (không cần Postgres cho test này —
# registry integration test riêng ở tests/integration/test_prompt_registry.py)
_P1 = next(s for s in SEED_PROMPTS if s["prompt_version"] == "p1_grounded_v1")
_PROVIDER = StaticPromptProvider(template=_P1["template"], version="p1_grounded_v1")


def _fake_embed(question: str) -> list[float]:
    # Vector giả chiều 768 — dense branch trả kết quả vô nghĩa nhưng hợp lệ;
    # sparse branch (BM25 thật) vẫn kéo được chunk đúng cho câu hỏi trong domain.
    return [0.01] * 768


@pytest.fixture(scope="module")
def service() -> RagService:
    return RagService(
        gateway=MockGateway(), qdrant_url=QDRANT_URL,
        prompt_provider=_PROVIDER, embed_fn=_fake_embed,
    )


def test_in_domain_question_returns_answer_with_citation(service):
    resp = service.answer(QARequest(question="Điều kiện tốt nghiệp đại học cần những gì?"))
    assert resp.trace_id.startswith("trace_")
    assert resp.request_id.startswith("req_")
    assert not resp.refusal
    assert resp.citations, "câu trong domain phải có citation"
    assert resp.model.provider == "mock"
    assert resp.confidence is not None and 0.0 <= resp.confidence <= 1.0
    # citation phải trỏ về chunk THẬT đã retrieve, không bịa
    trace = service.get_trace(resp.trace_id)
    retrieved_ids = {r["chunk_id"] for r in trace["retrieved"]}
    assert all(c.chunk_id in retrieved_ids for c in resp.citations)


def test_debug_mode_returns_retrieved_chunks_and_versions(service):
    resp = service.answer(QARequest(question="Học phí được miễn giảm thế nào?", debug=True))
    assert resp.retrieved_chunks, "debug phải trả retrieved chunks"
    assert resp.prompt_version == "p1_grounded_v1"
    assert resp.retrieval_config_id == "hybrid_dbsf_v2"
    assert resp.data_version and resp.index_version


def test_model_refusal_passes_through(service):
    refusing = RagService(
        gateway=MockGateway(refuse=True), qdrant_url=QDRANT_URL,
        prompt_provider=_PROVIDER, embed_fn=_fake_embed,
    )
    resp = refusing.answer(QARequest(question="Quy định về ký túc xá sao Hỏa?"))
    assert resp.refusal
    assert resp.citations == []
    assert resp.answer  # vẫn có message giải thích cho user
    assert resp.confidence is None  # không có "độ tin cậy của việc từ chối"


def test_pre_llm_refusal_on_low_score(service, monkeypatch):
    """min_score enforcement (calibrated 2026-07-13, xem config/retrieval.yaml
    + src/rag/service.py docstring) — điểm DBSF đỉnh dưới threshold phải
    refuse TRƯỚC khi gọi LLM, không tốn generation call."""
    import src.rag.service as service_mod

    def _fake_retrieve(*args, **kwargs):
        return [{"chunk_id": "chunk_fake_low_score", "score": 0.01, "text": "x"}] * 3

    monkeypatch.setattr(service_mod, "retrieve", _fake_retrieve)
    resp = service.answer(QARequest(question="Câu hỏi bất kỳ trong domain"))
    assert resp.refusal is True
    assert resp.model.provider == "none"  # không gọi LLM
    trace = service.get_trace(resp.trace_id)
    assert trace["refusal_stage"] == "pre_llm"
    assert trace["error_labels"] == ["low_score"]


def test_trace_recorded_with_versions(service):
    resp = service.answer(QARequest(question="Sinh viên bị cảnh báo học vụ khi nào?"))
    trace = service.get_trace(resp.trace_id)
    assert trace is not None
    assert trace["retrieval_config_id"] == "hybrid_dbsf_v2"
    assert trace["prompt_version"] == "p1_grounded_v1"
    assert trace["data_version"] == "data_20260713"
    assert trace["retrieved"], "trace phải ghi danh sách chunk đã retrieve"
    assert "retrieval_ms" in trace
