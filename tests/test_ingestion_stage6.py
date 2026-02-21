"""Stage 6 tests for incremental/dedupe and error logging schema."""

from pathlib import Path

from ingestion.crawler import is_content_changed
from ingestion.db import migration_files


def test_is_content_changed_handles_hash_transitions():
    assert is_content_changed(existing_hash=None, new_hash=None) is True
    assert is_content_changed(existing_hash=None, new_hash="abc") is True
    assert is_content_changed(existing_hash="abc", new_hash=None) is True
    assert is_content_changed(existing_hash="abc", new_hash="def") is True
    assert is_content_changed(existing_hash="abc", new_hash="abc") is False


def test_stage6_migration_exists_and_contains_error_table_and_counters():
    migration = Path("ingestion/migrations/003_incremental_and_errors.sql")
    assert migration.exists()
    sql = migration.read_text(encoding="utf-8").lower()
    assert "alter table crawl_runs" in sql
    assert "pages_unchanged" in sql
    assert "pages_skipped" in sql
    assert "create table if not exists crawl_errors" in sql


def test_migration_discovery_includes_stage6_migration():
    names = [f.name for f in migration_files()]
    assert "003_incremental_and_errors.sql" in names


def test_content_change_false_when_hashes_match():
    assert is_content_changed(existing_hash="abc123", new_hash="abc123") is False
