"""Integration test cho prompt registry (Phase 6) — Postgres THẬT.

Tự skip khi Postgres chưa chạy. Dùng prompt_id riêng cho test
(test_qa_vi_*) và dọn sạch sau mỗi test — không đụng registry rag_qa_vi
thật đã seed.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest

from src.common.settings import get_settings
from src.promptops.registry import PromptRegistry, PromptVersion, RegistryError

DSN = get_settings().postgres_dsn


def _postgres_ready() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _postgres_ready(), reason="Postgres not running")


@pytest.fixture
def registry():
    reg = PromptRegistry(DSN)
    prompt_id = f"test_qa_vi_{uuid.uuid4().hex[:8]}"
    yield reg, prompt_id
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM prompts WHERE prompt_id = %s", (prompt_id,))
        conn.commit()


def _version(prompt_id: str, version: str, status: str = "testing") -> PromptVersion:
    return PromptVersion(
        prompt_id=prompt_id, prompt_version=version, task_type="qa",
        domain="test", language="vi", model_tier="balanced",
        template="NGỮ CẢNH: {context}\nCÂU HỎI: {question}",
        variables=["context", "question"], created_by="pytest", status=status,
    )


def test_create_get_list_roundtrip(registry):
    reg, pid = registry
    assert reg.create_version(_version(pid, "v1"))
    got = reg.get(pid, "v1")
    assert got.template.startswith("NGỮ CẢNH")
    assert got.variables == ["context", "question"]
    versions = reg.list_versions(pid)
    assert [v["prompt_version"] for v in versions] == ["v1"]


def test_create_if_absent_is_idempotent(registry):
    reg, pid = registry
    assert reg.create_version(_version(pid, "v1"), if_absent=True) is True
    assert reg.create_version(_version(pid, "v1"), if_absent=True) is False


def test_invalid_template_rejected_at_write_time(registry):
    reg, pid = registry
    bad = _version(pid, "v_bad")
    bad.template = "chỉ có {context}, thiếu question"
    with pytest.raises(Exception, match="declared but unused"):
        reg.create_version(bad)


def test_activate_requires_eval_result_unless_override(registry):
    reg, pid = registry
    reg.create_version(_version(pid, "v1"))

    with pytest.raises(RegistryError, match="no eval_result_id"):
        reg.activate(pid, "v1", actor="pytest")

    with pytest.raises(RegistryError, match="override_reason"):
        reg.activate(pid, "v1", actor="pytest", override=True)

    reg.activate(pid, "v1", actor="pytest", override=True, override_reason="unit bootstrap")
    active = reg.get_active(pid)
    assert active.prompt_version == "v1"
    assert "override by pytest" in reg.get(pid, "v1").change_summary


def test_activate_with_eval_result_and_single_active(registry):
    reg, pid = registry
    reg.create_version(_version(pid, "v1"))
    reg.create_version(_version(pid, "v2"))
    reg.set_eval_result(pid, "v1", "cmp_001")
    reg.set_eval_result(pid, "v2", "cmp_001")

    reg.activate(pid, "v1", actor="pytest")
    assert reg.get_active(pid).prompt_version == "v1"

    reg.activate(pid, "v2", actor="pytest")
    assert reg.get_active(pid).prompt_version == "v2"
    # v1 phải bị archive — chỉ 1 active/prompt_id
    statuses = {v["prompt_version"]: v["status"] for v in reg.list_versions(pid)}
    assert statuses == {"v1": "archived", "v2": "active"}
