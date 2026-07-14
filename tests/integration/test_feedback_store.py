"""Integration test cho feedback store (Phase 11) — Postgres THẬT.

Tự skip khi Postgres chưa chạy, giống tests/integration/test_prompt_registry.py.
Dùng trace_id riêng cho test (test_trace_*) và dọn sạch sau mỗi test.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest

from src.common.settings import get_settings
from src.feedback.store import FeedbackStore, FeedbackStoreError
from src.rag.trace_store import new_id

DSN = get_settings().postgres_dsn


def _postgres_ready() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _postgres_ready(), reason="Postgres not running")


@pytest.fixture
def store():
    s = FeedbackStore(DSN)
    trace_id = f"test_trace_{uuid.uuid4().hex[:8]}"
    created_ids: list[str] = []

    def _create(**overrides):
        fid = new_id("test_fb")
        created_ids.append(fid)
        kwargs = {
            "feedback_id": fid, "trace_id": trace_id, "feedback_type": "missing_citation",
            "error_label": "citation_error",
        }
        kwargs.update(overrides)
        return s.create(**kwargs)

    yield s, _create, trace_id

    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM feedback WHERE feedback_id = ANY(%s)", (created_ids,))
        conn.commit()


def test_create_get_roundtrip(store):
    s, create, trace_id = store
    record = create(comment="thiếu citation vế 2")
    got = s.get(record.feedback_id)
    assert got.trace_id == trace_id
    assert got.error_label == "citation_error"
    assert got.comment == "thiếu citation vế 2"
    assert got.status == "open"
    assert got.source == "user"


def test_thumbs_up_allows_null_error_label(store):
    s, create, _ = store
    record = create(feedback_type="thumbs_up", error_label=None)
    got = s.get(record.feedback_id)
    assert got.error_label is None


def test_list_open_only_returns_open(store):
    s, create, _ = store
    r1 = create()
    r2 = create()
    s.mark_reviewed(r2.feedback_id, reviewer="pytest")
    open_ids = {r.feedback_id for r in s.list_open()}
    assert r1.feedback_id in open_ids
    assert r2.feedback_id not in open_ids


def test_mark_reviewed_sets_fields(store):
    s, create, _ = store
    record = create()
    s.mark_reviewed(record.feedback_id, reviewer="pytest", note="đã xử lý")
    got = s.get(record.feedback_id)
    assert got.status == "reviewed"
    assert got.reviewed_by == "pytest"
    assert got.review_note == "đã xử lý"
    assert got.reviewed_at is not None


def test_mark_reviewed_missing_id_raises(store):
    s, _create, _ = store
    with pytest.raises(FeedbackStoreError):
        s.mark_reviewed("fb_does_not_exist", reviewer="pytest")


def test_eval_seed_source_recorded(store):
    s, create, _ = store
    record = create(source="eval_seed", category="multi_hop")
    got = s.get(record.feedback_id)
    assert got.source == "eval_seed"
    assert got.category == "multi_hop"
