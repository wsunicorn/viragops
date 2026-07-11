"""Prompt registry — PostgreSQL-backed CRUD + activation policy (Module 4).

Enforcement rules from modules/04_promptops.md, implemented here so no
caller can bypass them:
- runtime resolves the active prompt from THIS registry, never from code;
- a version cannot become `active` without an `eval_result_id`, unless
  the caller passes an explicit, logged override (contract: "Chỉ cho phép
  activate nếu quality gate PASS hoặc có override được ghi log");
- exactly one active version per prompt_id (DB partial unique index
  backs this up even against racing writers);
- templates are validated against their declared variables at write time
  (renderer.validate_template) — bad data never reaches the runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import psycopg

from src.promptops.renderer import validate_template


@dataclass
class PromptVersion:
    prompt_id: str
    prompt_version: str
    task_type: str
    domain: str
    language: str
    model_tier: str
    template: str
    variables: list[str]
    created_by: str
    status: str
    parent_version: str | None = None
    change_summary: str | None = None
    eval_result_id: str | None = None


class RegistryError(RuntimeError):
    pass


_COLUMNS = (
    "prompt_id, prompt_version, task_type, domain, language, model_tier, template, "
    "variables, created_by, status, parent_version, change_summary, eval_result_id"
)


def _row_to_version(row: tuple) -> PromptVersion:
    data = dict(zip(_COLUMNS.replace(" ", "").split(","), row, strict=True))
    if isinstance(data["variables"], str):
        data["variables"] = json.loads(data["variables"])
    return PromptVersion(**data)


class PromptRegistry:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self):
        return psycopg.connect(self._dsn)

    def create_version(self, version: PromptVersion, if_absent: bool = False) -> bool:
        """Insert a new draft/testing version. Returns False when
        if_absent=True and the version already exists (idempotent seeding)."""
        validate_template(version.template, version.variables)
        if version.status == "active":
            raise RegistryError("new versions start as draft/testing — activate via activate()")

        with self._connect() as conn, conn.cursor() as cur:
            if if_absent:
                cur.execute(
                    "SELECT 1 FROM prompts WHERE prompt_id=%s AND prompt_version=%s",
                    (version.prompt_id, version.prompt_version),
                )
                if cur.fetchone():
                    return False
            cur.execute(
                f"INSERT INTO prompts ({_COLUMNS}) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    version.prompt_id, version.prompt_version, version.task_type,
                    version.domain, version.language, version.model_tier, version.template,
                    json.dumps(version.variables), version.created_by, version.status,
                    version.parent_version, version.change_summary, version.eval_result_id,
                ),
            )
            conn.commit()
        return True

    def get(self, prompt_id: str, prompt_version: str) -> PromptVersion:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM prompts WHERE prompt_id=%s AND prompt_version=%s",
                (prompt_id, prompt_version),
            )
            row = cur.fetchone()
        if row is None:
            raise RegistryError(f"prompt {prompt_id}/{prompt_version} not found")
        return _row_to_version(row)

    def list_versions(self, prompt_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT prompt_version, status, created_by, created_at, change_summary, "
                "eval_result_id, activated_at FROM prompts WHERE prompt_id=%s "
                "ORDER BY created_at",
                (prompt_id,),
            )
            rows = cur.fetchall()
        return [
            {
                "prompt_version": r[0], "status": r[1], "created_by": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
                "change_summary": r[4], "eval_result_id": r[5],
                "activated_at": r[6].isoformat() if r[6] else None,
            }
            for r in rows
        ]

    def get_active(self, prompt_id: str) -> PromptVersion:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM prompts WHERE prompt_id=%s AND status='active'",
                (prompt_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise RegistryError(
                f"no active version for prompt '{prompt_id}' — run scripts/seed_prompts.py "
                "and activate one via the comparison flow"
            )
        return _row_to_version(row)

    def set_eval_result(self, prompt_id: str, prompt_version: str, eval_result_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE prompts SET eval_result_id=%s WHERE prompt_id=%s AND prompt_version=%s",
                (eval_result_id, prompt_id, prompt_version),
            )
            if cur.rowcount == 0:
                raise RegistryError(f"prompt {prompt_id}/{prompt_version} not found")
            conn.commit()

    def activate(
        self,
        prompt_id: str,
        prompt_version: str,
        actor: str,
        override: bool = False,
        override_reason: str | None = None,
    ) -> None:
        target = self.get(prompt_id, prompt_version)
        if target.eval_result_id is None and not override:
            raise RegistryError(
                f"cannot activate {prompt_version}: no eval_result_id. "
                "Run a comparison/eval first, or pass an explicit logged override."
            )
        if override and not override_reason:
            raise RegistryError("override activation requires override_reason (logged)")

        note = (
            f"[override by {actor}: {override_reason}]"
            if override and target.eval_result_id is None
            else None
        )
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE prompts SET status='archived' "
                "WHERE prompt_id=%s AND status='active' AND prompt_version<>%s",
                (prompt_id, prompt_version),
            )
            if note:
                cur.execute(
                    "UPDATE prompts SET status='active', activated_at=%s, activated_by=%s, "
                    "change_summary = coalesce(change_summary,'') || ' ' || %s "
                    "WHERE prompt_id=%s AND prompt_version=%s",
                    (datetime.now(UTC), actor, note, prompt_id, prompt_version),
                )
            else:
                cur.execute(
                    "UPDATE prompts SET status='active', activated_at=%s, activated_by=%s "
                    "WHERE prompt_id=%s AND prompt_version=%s",
                    (datetime.now(UTC), actor, prompt_id, prompt_version),
                )
            conn.commit()
