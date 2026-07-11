-- Phase 3 (Module 1 DataOps/RAGOps) — documents/chunks metadata registry.
-- Postgres is the source of truth for document/chunk METADATA; vectors +
-- payload for retrieval live in Qdrant (see src/dataops/indexer.py). No
-- migration tool is set up yet (no alembic/ dir in this repo) — this is
-- applied directly via scripts/init_postgres_schema.py, idempotent via
-- IF NOT EXISTS, matching this project's current "no ORM yet" convention.

CREATE TABLE IF NOT EXISTS documents (
    document_id     TEXT PRIMARY KEY,
    domain          TEXT NOT NULL,
    title           TEXT NOT NULL,
    source_uri      TEXT,
    source_type     TEXT NOT NULL,
    source_version  TEXT NOT NULL,
    effective_date  DATE,
    ingested_at     TIMESTAMPTZ NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id            TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    data_version         TEXT NOT NULL,
    chunk_index          INTEGER NOT NULL,
    text                 TEXT NOT NULL,
    normalized_text      TEXT NOT NULL,
    token_count          INTEGER NOT NULL,
    page_start           INTEGER,
    page_end             INTEGER,
    section              TEXT,
    chunking_strategy    TEXT NOT NULL,
    parent_chunk_id      TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
    metadata             JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_data_version ON chunks (data_version);
CREATE INDEX IF NOT EXISTS idx_chunks_strategy ON chunks (chunking_strategy);
