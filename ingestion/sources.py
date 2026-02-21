"""Source management for ingestion domains."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CrawlSource:
    name: str
    domain: str
    start_urls: list[str]
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    max_depth: int = 2
    max_pages: int = 300
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


def startup_source_catalog() -> list[CrawlSource]:
    """Built-in startup knowledge source presets."""
    return [
        CrawlSource(
            name="hugo_love",
            domain="hugo.love",
            start_urls=[
                "https://hugo.love/",
            ],
            allowed_paths=[
                "/",
                "/about",
                "/blog",
                "/products",
                "/pricing",
                "/features",
            ],
            blocked_paths=[
                "/cdn-cgi",
                "/wp-admin",
                "/wp-login",
                "/cart",
                "/checkout",
                "/privacy",
                "/terms",
            ],
            max_depth=3,
            max_pages=400,
            is_active=False,
            metadata={
                "topic": "startup_case_study",
                "notes": "May be robots-restricted. Keep disabled by default.",
            },
        ),
        CrawlSource(
            name="paul_graham_essays",
            domain="paulgraham.com",
            start_urls=["https://paulgraham.com/articles.html"],
            allowed_paths=["/"],
            blocked_paths=[],
            max_depth=2,
            max_pages=200,
            is_active=True,
            metadata={"topic": "startup_strategy", "type": "essays"},
        ),
        CrawlSource(
            name="ycombinator_library",
            domain="www.ycombinator.com",
            start_urls=["https://www.ycombinator.com/library"],
            allowed_paths=["/library"],
            blocked_paths=["/apply", "/companies", "/jobs"],
            max_depth=2,
            max_pages=200,
            is_active=True,
            metadata={"topic": "startup_strategy", "type": "playbooks"},
        ),
        CrawlSource(
            name="a16z_speedrun",
            domain="speedrun.a16z.com",
            start_urls=["https://speedrun.a16z.com/"],
            allowed_paths=["/"],
            blocked_paths=[],
            max_depth=2,
            max_pages=180,
            is_active=True,
            metadata={"topic": "technical_startups", "type": "accelerator_content"},
        ),
        CrawlSource(
            name="sequoia_arc",
            domain="arc.sequoiacap.com",
            start_urls=["https://arc.sequoiacap.com/"],
            allowed_paths=["/"],
            blocked_paths=[],
            max_depth=2,
            max_pages=180,
            is_active=True,
            metadata={"topic": "ops", "type": "frameworks"},
        ),
        CrawlSource(
            name="stripe_atlas_guides",
            domain="stripe.com",
            start_urls=["https://stripe.com/atlas/guides"],
            allowed_paths=["/atlas/guides", "/atlas"],
            blocked_paths=["/pricing"],
            max_depth=2,
            max_pages=140,
            is_active=True,
            metadata={"topic": "fundraising", "type": "company_formation"},
        ),
        CrawlSource(
            name="reforge_blog",
            domain="www.reforge.com",
            start_urls=["https://www.reforge.com/blog"],
            allowed_paths=["/blog"],
            blocked_paths=[],
            max_depth=2,
            max_pages=120,
            is_active=True,
            metadata={"topic": "growth", "type": "growth_strategy"},
        ),
        CrawlSource(
            name="lenny_newsletter_public",
            domain="www.lennysnewsletter.com",
            start_urls=["https://www.lennysnewsletter.com/"],
            allowed_paths=["/p/"],
            blocked_paths=["/api"],
            max_depth=1,
            max_pages=120,
            is_active=True,
            metadata={"topic": "product", "type": "product_growth"},
        ),
        CrawlSource(
            name="saastr_blog",
            domain="www.saastr.com",
            start_urls=["https://www.saastr.com/blog/"],
            allowed_paths=["/blog"],
            blocked_paths=[],
            max_depth=2,
            max_pages=180,
            is_active=True,
            metadata={"topic": "go_to_market", "type": "saas_scaling"},
        ),
    ]


def default_sources() -> list[CrawlSource]:
    """
    Backward-compatible alias retained from Stage 2.
    """
    return startup_source_catalog()


def _insert_or_update_source_sql() -> str:
    return """
        INSERT INTO sources (
            name, domain, start_urls, allowed_paths, blocked_paths,
            max_depth, max_pages, is_active, metadata
        ) VALUES (
            %(name)s, %(domain)s, %(start_urls)s, %(allowed_paths)s, %(blocked_paths)s,
            %(max_depth)s, %(max_pages)s, %(is_active)s, %(metadata)s
        )
        ON CONFLICT (name)
        DO UPDATE SET
            domain = EXCLUDED.domain,
            start_urls = EXCLUDED.start_urls,
            allowed_paths = EXCLUDED.allowed_paths,
            blocked_paths = EXCLUDED.blocked_paths,
            max_depth = EXCLUDED.max_depth,
            max_pages = EXCLUDED.max_pages,
            is_active = EXCLUDED.is_active,
            metadata = EXCLUDED.metadata,
            updated_at = NOW();
    """


def upsert_source(source: CrawlSource) -> None:
    """
    Insert or update a single crawl source definition.
    """
    try:
        import psycopg
        from psycopg.types.json import Json
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required for source onboarding. "
            "Install dependencies from requirements.txt."
        ) from exc

    from config import get_settings

    settings = get_settings()
    sql = _insert_or_update_source_sql()
    with psycopg.connect(settings.postgres_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "name": source.name,
                    "domain": source.domain,
                    "start_urls": Json(source.start_urls),
                    "allowed_paths": Json(source.allowed_paths),
                    "blocked_paths": Json(source.blocked_paths),
                    "max_depth": source.max_depth,
                    "max_pages": source.max_pages,
                    "is_active": source.is_active,
                    "metadata": Json(source.metadata),
                },
            )
        conn.commit()


def list_sources(only_active: bool = False) -> list[dict[str, Any]]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for listing sources.") from exc

    from config import get_settings

    settings = get_settings()
    query = """
        SELECT id, name, domain, start_urls, allowed_paths, blocked_paths,
               max_depth, max_pages, is_active, metadata, created_at, updated_at
        FROM sources
    """
    params: tuple[Any, ...] = ()
    if only_active:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY id ASC"

    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_source(source_name: str) -> dict[str, Any] | None:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for reading sources.") from exc

    from config import get_settings

    settings = get_settings()
    query = """
        SELECT id, name, domain, start_urls, allowed_paths, blocked_paths,
               max_depth, max_pages, is_active, metadata, created_at, updated_at
        FROM sources
        WHERE name = %s
    """
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (source_name,))
            row = cur.fetchone()
    return dict(row) if row else None


def seed_default_sources() -> int:
    """
    Upsert default sources into PostgreSQL.

    Returns:
        Number of processed sources.
    """
    try:
        import psycopg
        from psycopg.types.json import Json
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required for source seeding. "
            "Install dependencies from requirements.txt."
        ) from exc

    from config import get_settings

    settings = get_settings()
    sources = startup_source_catalog()
    sql = _insert_or_update_source_sql()

    with psycopg.connect(settings.postgres_dsn) as conn:
        with conn.cursor() as cur:
            for source in sources:
                cur.execute(
                    sql,
                    {
                        "name": source.name,
                        "domain": source.domain,
                        "start_urls": Json(source.start_urls),
                        "allowed_paths": Json(source.allowed_paths),
                        "blocked_paths": Json(source.blocked_paths),
                        "max_depth": source.max_depth,
                        "max_pages": source.max_pages,
                        "is_active": source.is_active,
                        "metadata": Json(source.metadata),
                    },
                )
        conn.commit()

    return len(sources)
