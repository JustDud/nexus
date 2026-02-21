"""Monitoring helpers for ingestion pipeline (Stage 10)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from config import get_settings


def ingestion_metrics() -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion monitoring.") from exc

    s = get_settings()
    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total_sources FROM sources")
            total_sources = int(cur.fetchone()["total_sources"])

            cur.execute("SELECT COUNT(*) AS total_pages FROM pages")
            total_pages = int(cur.fetchone()["total_pages"])

            cur.execute("SELECT COUNT(*) AS total_chunks FROM chunks")
            total_chunks = int(cur.fetchone()["total_chunks"])

            cur.execute("SELECT COUNT(*) AS total_runs FROM crawl_runs")
            total_runs = int(cur.fetchone()["total_runs"])

            cur.execute("SELECT COUNT(*) AS total_errors FROM crawl_errors")
            total_errors = int(cur.fetchone()["total_errors"])

    return {
        "total_sources": total_sources,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "total_runs": total_runs,
        "total_errors": total_errors,
    }


def ingestion_health() -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion monitoring.") from exc

    s = get_settings()
    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, pages_fetched, pages_failed, started_at, finished_at
                FROM crawl_runs
                ORDER BY id DESC
                LIMIT 1
                """
            )
            latest = cur.fetchone()

    if latest is None:
        return {"status": "no_runs", "latest_run": None}

    latest_dict = dict(latest)
    status = "ok"
    if latest_dict["status"] == "failed":
        status = "degraded"
    elif latest_dict["pages_fetched"] == 0:
        status = "warning"

    return {"status": status, "latest_run": latest_dict}


def source_freshness(max_age_hours: int = 72) -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for ingestion monitoring.") from exc

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    s = get_settings()
    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    src.name AS source_name,
                    src.domain AS source_domain,
                    MAX(p.fetched_at) AS last_fetched_at
                FROM sources src
                LEFT JOIN pages p ON p.source_id = src.id
                GROUP BY src.name, src.domain
                ORDER BY src.name
                """
            )
            rows = cur.fetchall()

    sources = []
    stale_count = 0
    for row in rows:
        entry = dict(row)
        last = entry.get("last_fetched_at")
        is_stale = True
        if last is not None and last >= cutoff:
            is_stale = False
        if is_stale:
            stale_count += 1
        entry["is_stale"] = is_stale
        sources.append(entry)

    return {
        "max_age_hours": max_age_hours,
        "stale_count": stale_count,
        "sources": sources,
    }
