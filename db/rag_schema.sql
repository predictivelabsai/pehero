-- PEHero RAG schema. Idempotent. pgvector-backed retrieval over PE VDR
-- documents (CIMs, IC memos, MSAs, QoE reports, legal diligence, ESG reports,
-- industry reports, LP side letters).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS pehero_rag;

CREATE TABLE IF NOT EXISTS pehero_rag.documents (
    id           BIGSERIAL PRIMARY KEY,
    company_id   BIGINT,              -- soft reference to pehero.companies(id)
    doc_type     TEXT NOT NULL,       -- cim | msa | qoe | legal | esg | tax | tech_ddq | industry | lp_letter | ic_memo | misc
    title        TEXT NOT NULL,
    source_path  TEXT,
    metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_company_idx ON pehero_rag.documents(company_id);
CREATE INDEX IF NOT EXISTS documents_type_idx    ON pehero_rag.documents(doc_type);

CREATE TABLE IF NOT EXISTS pehero_rag.chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES pehero_rag.documents(id) ON DELETE CASCADE,
    ord          INTEGER NOT NULL,
    text         TEXT NOT NULL,
    token_count  INTEGER,
    metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (document_id, ord)
);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON pehero_rag.chunks(document_id);

-- Embedding dim parameterized at migration time via {{EMBEDDING_DIM}} —
-- db/migrate.py substitutes the value from EMBEDDING_DIM env var before
-- applying. If you change EMBEDDING_DIM, run `python -m db.migrate --drop`
-- (destroys RAG tables) and re-index.
CREATE TABLE IF NOT EXISTS pehero_rag.embeddings (
    chunk_id   BIGINT PRIMARY KEY REFERENCES pehero_rag.chunks(id) ON DELETE CASCADE,
    embedding  vector({{EMBEDDING_DIM}}) NOT NULL
);

-- ivfflat index is intentionally created AFTER bulk seeding (see
-- `rag.indexer.build_ann_index()`). ivfflat assigns rows to clusters when
-- it's built, so creating it before the table is populated gives empty or
-- near-empty cells and wrong results. For synthetic-scale (<10k chunks) a
-- sequential scan is fine; for larger corpora call build_ann_index() once
-- the table is loaded.

CREATE TABLE IF NOT EXISTS pehero_rag.rag_queries (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT,
    session_id  BIGINT,
    query       TEXT NOT NULL,
    top_k       INTEGER,
    filters     JSONB,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
