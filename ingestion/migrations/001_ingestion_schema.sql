-- Stage 1 ingestion schema
-- Safe to rerun because tables are created IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    start_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    allowed_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocked_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    max_depth INTEGER NOT NULL DEFAULT 2,
    max_pages INTEGER NOT NULL DEFAULT 300,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(is_active);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    pages_discovered INTEGER NOT NULL DEFAULT 0,
    pages_fetched INTEGER NOT NULL DEFAULT 0,
    pages_succeeded INTEGER NOT NULL DEFAULT 0,
    pages_failed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_source ON crawl_runs(source_id);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_status ON crawl_runs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_started_at ON crawl_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS pages (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    crawl_run_id BIGINT REFERENCES crawl_runs(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    canonical_url TEXT,
    status_code INTEGER,
    title TEXT,
    html_content TEXT,
    raw_text TEXT,
    cleaned_text TEXT,
    content_hash TEXT,
    fetched_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_id, url)
);

CREATE INDEX IF NOT EXISTS idx_pages_source ON pages(source_id);
CREATE INDEX IF NOT EXISTS idx_pages_crawl_run ON pages(crawl_run_id);
CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON pages(content_hash);
CREATE INDEX IF NOT EXISTS idx_pages_fetched_at ON pages(fetched_at DESC);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    page_id BIGINT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER,
    embedding_provider TEXT,
    embedding_model TEXT,
    vector_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (page_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(page_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_vector_id ON chunks(vector_id);
