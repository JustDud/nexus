"""Stage 5 tests for chunk/index payload preparation."""

from datetime import datetime, timezone

from ingestion.indexer import build_chunk_metadata, build_vector_id


def test_build_vector_id_is_deterministic():
    v1 = build_vector_id("hugo_love", 12, 3, "abcdef1234567890")
    v2 = build_vector_id("hugo_love", 12, 3, "abcdef1234567890")
    assert v1 == v2
    assert v1.startswith("crawl_hugo_love_12_3_abcdef123456")


def test_build_vector_id_handles_missing_hash():
    vector_id = build_vector_id("hugo_love", 1, 0, None)
    assert vector_id == "crawl_hugo_love_1_0_nohash"


def test_build_chunk_metadata_contains_citation_fields():
    page = {
        "id": 99,
        "url": "https://hugo.love/blog/post-1",
        "title": "Post title",
        "content_hash": "hash123",
        "fetched_at": datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc),
    }
    meta = build_chunk_metadata(source_name="hugo_love", page=page, chunk_index=4)
    assert meta["domain"] == "hugo_love"
    assert meta["source_file"] == "https://hugo.love/blog/post-1"
    assert meta["source_url"] == "https://hugo.love/blog/post-1"
    assert meta["chunk_index"] == 4
    assert meta["page_id"] == 99
    assert meta["title"] == "Post title"
    assert meta["content_hash"] == "hash123"
    assert meta["fetched_at"].startswith("2026-02-21T10:00:00")
