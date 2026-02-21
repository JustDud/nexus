"""Stage 9 tests for multi-source framework and onboarding."""

from pathlib import Path

from ingestion.db import migration_files
from ingestion.sources import startup_source_catalog


def test_startup_catalog_contains_multiple_sources():
    sources = startup_source_catalog()
    names = {s.name for s in sources}
    assert "hugo_love" in names
    assert "paul_graham_essays" in names
    assert "ycombinator_library" in names
    assert "a16z_speedrun" in names
    assert "sequoia_arc" in names
    assert "stripe_atlas_guides" in names
    assert "reforge_blog" in names
    assert "lenny_newsletter_public" in names
    assert "saastr_blog" in names
    assert len(sources) >= 9


def test_hugo_source_disabled_by_default_due_robots_risk():
    sources = startup_source_catalog()
    hugo = next(s for s in sources if s.name == "hugo_love")
    assert hugo.is_active is False


def test_stage9_migration_exists_and_seeds_startup_sources():
    migration = Path("ingestion/migrations/004_seed_startup_sources.sql")
    assert migration.exists()
    sql = migration.read_text(encoding="utf-8").lower()
    assert "'paul_graham_essays'" in sql
    assert "'ycombinator_library'" in sql
    assert "'a16z_speedrun'" in sql
    assert "on conflict (name)" in sql


def test_migration_discovery_includes_stage9():
    names = [f.name for f in migration_files()]
    assert "004_seed_startup_sources.sql" in names
    assert "005_seed_additional_startup_sources.sql" in names
