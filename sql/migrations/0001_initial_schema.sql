-- Phase 3 (Module 1 DataOps/RAGOps) — documents/chunks metadata registry,
-- + Phase 6 (Module 4 PromptOps) — prompt registry.
-- Postgres is the source of truth for document/chunk METADATA; vectors +
-- payload for retrieval live in Qdrant (see src/dataops/indexer.py).

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

-- Phase 6 (Module 4 PromptOps) — prompt registry. Metadata bắt buộc theo
-- docs/system/modules/04_promptops.md. Runtime CHỈ lấy prompt từ đây
-- (không hard-code trong code); template seed gốc nằm ở
-- src/promptops/templates.py và được ghi vào bảng qua scripts/seed_prompts.py.
CREATE TABLE IF NOT EXISTS prompts (
    prompt_id       TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,
    task_type       TEXT NOT NULL,
    domain          TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'vi',
    model_tier      TEXT NOT NULL DEFAULT 'balanced',
    template        TEXT NOT NULL,
    variables       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by      TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    status          TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'testing', 'active', 'archived')),
    parent_version  TEXT,
    change_summary  TEXT,
    eval_result_id  TEXT,
    activated_at    TIMESTAMPTZ,
    activated_by    TEXT,
    PRIMARY KEY (prompt_id, prompt_version)
);

-- Mỗi prompt_id chỉ có tối đa 1 version active.
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_one_active
    ON prompts (prompt_id) WHERE status = 'active';
