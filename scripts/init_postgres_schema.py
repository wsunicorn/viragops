"""Apply pending SQL migrations from sql/migrations/ to Postgres.

Replaces the old single-file sql/schema.sql approach (2026-07-13) — that
file was hand-edited in place on every schema change with no record of
WHEN or WHAT changed, only recoverable from git blame. This is a
lightweight migration runner, not a full ORM/Alembic setup (deliberately
— see docs/system/04_tech_stack_decisions.md "Hạn chế stack quá nặng nếu
không đóng góp cho LLMOps"; this project's Postgres usage is 3 tables):

- Each file in sql/migrations/ is named `NNNN_description.sql` (4-digit,
  zero-padded, sortable) and applied in filename order.
- A `schema_migrations` table (created here, bootstrap) records which
  filenames have been applied and when — `SELECT * FROM
  schema_migrations ORDER BY applied_at` gives a real, queryable history.
- Each migration file runs inside its own transaction; already-applied
  files are skipped. Migrations should stay idempotent (IF NOT EXISTS /
  IF EXISTS) so a partial-apply-then-rerun is still safe, matching this
  project's existing convention — this script does not try to enforce
  that for you.

Usage:
    python scripts/init_postgres_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402

MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"

_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def main() -> int:
    settings = get_settings()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print(f"No migration files found in {MIGRATIONS_DIR.relative_to(PROJECT_ROOT)}")
        return 1

    print(f"Connecting to postgres at {settings.postgres_host}:{settings.postgres_port}/"
          f"{settings.postgres_db} ...")
    try:
        with psycopg.connect(settings.postgres_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(_BOOTSTRAP_SQL)
                cur.execute("SELECT filename FROM schema_migrations")
                applied = {row[0] for row in cur.fetchall()}
            conn.commit()

            for path in migration_files:
                if path.name in applied:
                    print(f"  [skip]  {path.name} (already applied)")
                    continue
                with conn.cursor() as cur:
                    cur.execute(path.read_text(encoding="utf-8"))
                    cur.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                    )
                conn.commit()
                print(f"  [apply] {path.name}")
    except psycopg.OperationalError as exc:
        print(f"FAILED to connect/apply migrations: {exc}")
        return 1

    print(f"Schema up to date ({len(migration_files)} migration file(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
