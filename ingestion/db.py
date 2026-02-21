"""PostgreSQL helpers for ingestion pipeline schema and migrations."""

from pathlib import Path

from config import get_settings


def migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "migrations"


def migration_files() -> list[Path]:
    return sorted(migrations_dir().glob("*.sql"))


def apply_migrations() -> int:
    """
    Apply SQL migration files in lexical order.

    Returns:
        Number of migration files applied.
    """
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required for ingestion DB migrations. "
            "Install dependencies from requirements.txt."
        ) from exc

    settings = get_settings()
    files = migration_files()
    if not files:
        return 0

    applied = 0
    with psycopg.connect(settings.postgres_dsn) as conn:
        with conn.cursor() as cur:
            for file in files:
                sql = file.read_text(encoding="utf-8")
                cur.execute(sql)
                applied += 1
        conn.commit()

    return applied
