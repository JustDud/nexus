-- Stage 6: incremental crawl counters and durable error log.

ALTER TABLE crawl_runs
ADD COLUMN IF NOT EXISTS pages_unchanged INTEGER NOT NULL DEFAULT 0;

ALTER TABLE crawl_runs
ADD COLUMN IF NOT EXISTS pages_skipped INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS crawl_errors (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    crawl_run_id BIGINT NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
    url TEXT,
    error_type TEXT NOT NULL,
    message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crawl_errors_run ON crawl_errors(crawl_run_id);
CREATE INDEX IF NOT EXISTS idx_crawl_errors_source ON crawl_errors(source_id);
CREATE INDEX IF NOT EXISTS idx_crawl_errors_type ON crawl_errors(error_type);
