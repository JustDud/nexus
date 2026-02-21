"""Stage 8 tests for retrieval filter building."""

from rag.retriever import _build_where_filter


def test_where_filter_none_when_no_filters():
    assert _build_where_filter(None, None, None, None) is None


def test_where_filter_domain_only():
    where = _build_where_filter(domain="market", source_names=None, topic_tags=None, max_age_hours=None)
    assert where == {"domain": "market"}


def test_where_filter_source_names_and_topics_and_freshness():
    where = _build_where_filter(
        domain=None,
        source_names=["ycombinator_library", "a16z_speedrun"],
        topic_tags=["startup_strategy"],
        max_age_hours=24,
    )
    assert "$and" in where
    parts = where["$and"]
    assert any(p.get("domain", {}).get("$in") == ["ycombinator_library", "a16z_speedrun"] for p in parts)
    assert any(p.get("topic") == "startup_strategy" for p in parts)
    assert any("fetched_at" in p for p in parts)
