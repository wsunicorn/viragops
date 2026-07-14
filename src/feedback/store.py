"""Feedback store — PostgreSQL-backed CRUD (Module 9), same connection
shape as src/promptops/registry.py (bare psycopg, no pool, one short-lived
connection per call, parameterized %s SQL, explicit commit)."""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg

from src.feedback.schemas import ErrorLabel, FeedbackRecord, FeedbackType, Source

_COLUMNS = (
    "feedback_id, trace_id, feedback_type, comment, rating, error_label, "
    "category, source, status, reviewed_by, reviewed_at, review_note, created_at"
)


def _row_to_record(row: tuple) -> FeedbackRecord:
    data = dict(zip(_COLUMNS.replace(" ", "").split(","), row, strict=True))
    data["created_at"] = data["created_at"].isoformat() if data["created_at"] else None
    data["reviewed_at"] = data["reviewed_at"].isoformat() if data["reviewed_at"] else None
    return FeedbackRecord(**data)


class FeedbackStoreError(RuntimeError):
    pass


class FeedbackStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self):
        return psycopg.connect(self._dsn)

    def create(
        self,
        feedback_id: str,
        trace_id: str,
        feedback_type: FeedbackType,
        error_label: ErrorLabel | None,
        comment: str | None = None,
        rating: int | None = None,
        category: str | None = None,
        source: Source = "user",
    ) -> FeedbackRecord:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (feedback_id, trace_id, feedback_type, comment, "
                "rating, error_label, category, source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (feedback_id, trace_id, feedback_type, comment, rating, error_label, category, source),
            )
            conn.commit()
        return self.get(feedback_id)

    def get(self, feedback_id: str) -> FeedbackRecord:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {_COLUMNS} FROM feedback WHERE feedback_id=%s", (feedback_id,))
            row = cur.fetchone()
        if row is None:
            raise FeedbackStoreError(f"feedback {feedback_id} not found")
        return _row_to_record(row)

    def list_open(self) -> list[FeedbackRecord]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {_COLUMNS} FROM feedback WHERE status='open' ORDER BY created_at")
            rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def list_all(self) -> list[FeedbackRecord]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {_COLUMNS} FROM feedback ORDER BY created_at")
            rows = cur.fetchall()
        return [_row_to_record(r) for r in rows]

    def mark_reviewed(
        self, feedback_id: str, reviewer: str, note: str | None = None, status: str = "reviewed"
    ) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE feedback SET status=%s, reviewed_by=%s, reviewed_at=%s, review_note=%s "
                "WHERE feedback_id=%s",
                (status, reviewer, datetime.now(UTC), note, feedback_id),
            )
            if cur.rowcount == 0:
                raise FeedbackStoreError(f"feedback {feedback_id} not found")
            conn.commit()
