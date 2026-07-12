"""Integration test cho Evaluation Engine runner (Phase 8) — Qdrant THẬT +
gateway MOCK, judge=None. Chạy được khi docker compose up (qdrant) và đã
ingest (Phase 3). Tự skip khi Qdrant/collection/manifest chưa sẵn sàng —
không fail CI nơi không có service. Test này chỉ verify wiring (retrieval
eval, context precision, citation accuracy, refusal check đúng shape) —
KHÔNG gọi judge thật (tốn quota), test đó thuộc phần chạy tay
`scripts/run_evaluation.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from src.promptops.templates import SEED_PROMPTS
from src.rag.gateway_client import MockGateway
from src.rag.prompt_builder import StaticPromptProvider
from src.rag.service import RagService
from src.retrieval.citation_matcher import group_chunks_by_document

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
QDRANT_URL = "http://localhost:6333"


def _qdrant_ready() -> bool:
    try:
        return httpx.get(f"{QDRANT_URL}/collections", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


def _manifest() -> dict | None:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        return None
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


pytestmark = pytest.mark.skipif(not _qdrant_ready() or _manifest() is None, reason="Qdrant/manifest not ready")

_P1 = next(s for s in SEED_PROMPTS if s["prompt_version"] == "p1_grounded_v1")
_PROVIDER = StaticPromptProvider(template=_P1["template"], version="p1_grounded_v1")


def _fake_embed(question: str) -> list[float]:
    return [0.01] * 768


@pytest.fixture(scope="module")
def assets():
    manifest = _manifest()
    chunks_path = CHUNKS_DIR / f"{manifest['chunking_strategy_indexed']}_{manifest['data_version']}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    chunks_by_doc = group_chunks_by_document(chunks)
    chunk_text_by_id = {c["chunk_id"]: c["text"] for c in chunks}
    service = RagService(
        gateway=MockGateway(), qdrant_url=QDRANT_URL,
        prompt_provider=_PROVIDER, embed_fn=_fake_embed,
    )
    return service, chunks_by_doc, chunk_text_by_id


def test_run_question_in_domain(assets):
    from src.evaluation.runner import run_question

    service, chunks_by_doc, chunk_text_by_id = assets
    item = {
        "id": "q_test_indomain",
        "question": "Điều kiện tốt nghiệp đại học cần những gì?",
        "category": "factoid",
        "requires_refusal": False,
        "requires_clarification": False,
        "expected_citations": [],
        "ground_truth": "",
    }
    result = run_question(service, None, item, chunks_by_doc, chunk_text_by_id, eval_k=5)

    assert result.question_id == "q_test_indomain"
    assert result.got_refusal is False
    assert result.refusal_correct is True
    assert result.judge is None  # judge=None -> không gọi
    assert result.trace_id.startswith("trace_")


def test_run_question_expected_refusal(assets):
    from src.evaluation.runner import run_question

    service, chunks_by_doc, chunk_text_by_id = assets
    refusing_service = RagService(
        gateway=MockGateway(refuse=True), qdrant_url=QDRANT_URL,
        prompt_provider=_PROVIDER, embed_fn=_fake_embed,
    )
    item = {
        "id": "q_test_refusal",
        "question": "Trường có cho nuôi thú cưng trong ký túc xá không?",
        "category": "out_of_scope",
        "requires_refusal": True,
        "requires_clarification": False,
        "expected_citations": [],
        "ground_truth": "",
    }
    result = run_question(refusing_service, None, item, chunks_by_doc, chunk_text_by_id, eval_k=5)

    assert result.got_refusal is True
    assert result.refusal_correct is True
    assert result.citation_accuracy is None  # refusal -> không chấm citation accuracy


def test_aggregate_shapes():
    from src.evaluation.runner import aggregate

    agg = aggregate([])
    assert agg == {"n_questions": 0}
