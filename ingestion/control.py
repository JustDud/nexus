"""Service layer for ingestion control endpoints (Stage 7)."""

from typing import Any

from config import get_settings
from ingestion.crawler import BasicCrawler
from ingestion.indexer import index_cleaned_pages
from ingestion.manual_import import import_directory
from ingestion.sources import CrawlSource, get_source, list_sources, upsert_source


def start_ingestion(source_name: str, index_after_crawl: bool) -> dict[str, Any]:
    crawler_stats = BasicCrawler().crawl_source(source_name)
    result: dict[str, Any] = {
        "source_name": source_name,
        "crawl_run_id": crawler_stats.run_id,
        "crawl": {
            "pages_discovered": crawler_stats.pages_discovered,
            "pages_fetched": crawler_stats.pages_fetched,
            "pages_succeeded": crawler_stats.pages_succeeded,
            "pages_failed": crawler_stats.pages_failed,
            "pages_unchanged": crawler_stats.pages_unchanged,
            "pages_skipped": crawler_stats.pages_skipped,
        },
    }
    if index_after_crawl:
        indexed = index_cleaned_pages(source_name=source_name)
        result["indexing"] = {
            "pages_indexed": indexed.pages_indexed,
            "total_chunks": indexed.total_chunks,
            "pages_skipped_unchanged": indexed.pages_skipped_unchanged,
        }
    return result


def list_runs(limit: int = 50, source_name: str | None = None) -> list[dict[str, Any]]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion control routes.") from exc

    s = get_settings()
    query = """
        SELECT
            cr.id,
            cr.source_id,
            src.name AS source_name,
            src.domain AS source_domain,
            cr.status,
            cr.started_at,
            cr.finished_at,
            cr.pages_discovered,
            cr.pages_fetched,
            cr.pages_succeeded,
            cr.pages_failed,
            cr.pages_unchanged,
            cr.pages_skipped,
            cr.error_message
        FROM crawl_runs cr
        JOIN sources src ON src.id = cr.source_id
    """
    params: list[Any] = []
    if source_name:
        query += " WHERE src.name = %s"
        params.append(source_name)
    query += " ORDER BY cr.id DESC LIMIT %s"
    params.append(limit)

    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_run(run_id: int) -> dict[str, Any] | None:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion control routes.") from exc

    s = get_settings()
    query = """
        SELECT
            cr.id,
            cr.source_id,
            src.name AS source_name,
            src.domain AS source_domain,
            cr.status,
            cr.started_at,
            cr.finished_at,
            cr.pages_discovered,
            cr.pages_fetched,
            cr.pages_succeeded,
            cr.pages_failed,
            cr.pages_unchanged,
            cr.pages_skipped,
            cr.error_message
        FROM crawl_runs cr
        JOIN sources src ON src.id = cr.source_id
        WHERE cr.id = %s
    """
    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def get_run_errors(run_id: int, limit: int = 200) -> list[dict[str, Any]]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion control routes.") from exc

    s = get_settings()
    query = """
        SELECT
            id,
            source_id,
            crawl_run_id,
            url,
            error_type,
            message,
            metadata,
            created_at
        FROM crawl_errors
        WHERE crawl_run_id = %s
        ORDER BY id DESC
        LIMIT %s
    """
    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id, limit))
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def start_ingestion_batch(
    source_names: list[str] | None,
    only_active: bool,
    index_after_crawl: bool,
    stop_on_error: bool,
) -> dict[str, Any]:
    available_sources = list_sources(only_active=only_active)
    if source_names:
        allowed = set(source_names)
        selected = [s for s in available_sources if s["name"] in allowed]
    else:
        selected = available_sources

    if not selected:
        return {"results": [], "count": 0}

    results: list[dict[str, Any]] = []
    for source in selected:
        source_name = source["name"]
        try:
            result = start_ingestion(source_name=source_name, index_after_crawl=index_after_crawl)
            result["status"] = "ok"
            results.append(result)
        except Exception as exc:
            results.append(
                {
                    "source_name": source_name,
                    "status": "error",
                    "error": str(exc),
                }
            )
            if stop_on_error:
                break
    return {"results": results, "count": len(results)}


def onboard_source(payload: dict[str, Any]) -> dict[str, Any]:
    source = CrawlSource(
        name=payload["name"],
        domain=payload["domain"],
        start_urls=payload["start_urls"],
        allowed_paths=payload.get("allowed_paths", []),
        blocked_paths=payload.get("blocked_paths", []),
        max_depth=payload.get("max_depth", 2),
        max_pages=payload.get("max_pages", 300),
        is_active=payload.get("is_active", True),
        metadata=payload.get("metadata", {}),
    )
    upsert_source(source)
    stored = get_source(source_name=source.name)
    if stored is None:
        raise RuntimeError("Failed to read source after upsert.")
    return stored


def import_local_directory(
    directory: str,
    source_name: str,
    topic: str,
    recursive: bool,
    index_after_import: bool,
) -> dict[str, Any]:
    return import_directory(
        directory=directory,
        source_name=source_name,
        topic=topic,
        recursive=recursive,
        index_after_import=index_after_import,
    )
