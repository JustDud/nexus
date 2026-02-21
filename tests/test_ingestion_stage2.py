"""Stage 2 tests for source management and hugo.love seed."""

from pathlib import Path


def test_default_sources_include_hugo_love():
    from ingestion.sources import default_sources

    sources = default_sources()
    hugo = next(s for s in sources if s.name == "hugo_love")
    assert hugo.domain == "hugo.love"
    assert "https://hugo.love/" in hugo.start_urls
    assert "/blog" in hugo.allowed_paths
    assert "/checkout" in hugo.blocked_paths
    assert hugo.max_depth == 3
    assert hugo.max_pages == 400


def test_stage2_seed_migration_exists_and_mentions_hugo():
    migration_file = Path("ingestion/migrations/002_seed_hugo_love_source.sql")
    assert migration_file.exists()
    sql = migration_file.read_text(encoding="utf-8").lower()
    assert "insert into sources" in sql
    assert "'hugo_love'" in sql
    assert "'hugo.love'" in sql
    assert "on conflict (name)" in sql


def test_migration_discovery_includes_stage2_seed():
    from ingestion.db import migration_files

    names = [path.name for path in migration_files()]
    assert "001_ingestion_schema.sql" in names
    assert "002_seed_hugo_love_source.sql" in names
