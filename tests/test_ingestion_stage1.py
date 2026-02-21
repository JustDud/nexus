"""Stage 1 tests for ingestion schema foundation."""

from pathlib import Path


def test_ingestion_migration_file_exists():
    migration_file = Path("ingestion/migrations/001_ingestion_schema.sql")
    assert migration_file.exists()


def test_ingestion_migration_contains_core_tables():
    migration_file = Path("ingestion/migrations/001_ingestion_schema.sql")
    sql = migration_file.read_text(encoding="utf-8").lower()
    assert "create table if not exists sources" in sql
    assert "create table if not exists crawl_runs" in sql
    assert "create table if not exists pages" in sql
    assert "create table if not exists chunks" in sql


def test_migration_discovery_finds_sql_files():
    from ingestion.db import migration_files

    files = migration_files()
    assert files
    assert files[0].name == "001_ingestion_schema.sql"
