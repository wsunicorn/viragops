"""Apply sql/schema.sql to the Postgres instance from docker-compose.

Idempotent (CREATE TABLE IF NOT EXISTS) — safe to rerun. Uses
src.common.settings.get_settings() for connection info, same as the API
runtime, instead of reading POSTGRES_* env vars a second time.

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

SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def main() -> int:
    settings = get_settings()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    print(f"Connecting to postgres at {settings.postgres_host}:{settings.postgres_port}/"
          f"{settings.postgres_db} ...")
    try:
        with psycopg.connect(settings.postgres_dsn) as conn, conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
    except psycopg.OperationalError as exc:
        print(f"FAILED to connect/apply schema: {exc}")
        return 1

    print(f"Schema applied OK from {SCHEMA_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
