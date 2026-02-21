"""Tests for Stage 7 ingestion control API routes."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_start_ingestion_success(client, monkeypatch):
    def fake_start_ingestion(source_name: str, index_after_crawl: bool):
        return {
            "source_name": source_name,
            "crawl_run_id": 123,
            "crawl": {"pages_fetched": 5},
            "indexing": {"pages_indexed": 2} if index_after_crawl else None,
        }

    monkeypatch.setattr("api.ingestion_routes.start_ingestion", fake_start_ingestion)
    resp = client.post("/api/ingestion/start", json={"source_name": "hugo_love", "index_after_crawl": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_name"] == "hugo_love"
    assert body["crawl_run_id"] == 123


def test_start_ingestion_unknown_source_returns_404(client, monkeypatch):
    def fake_start_ingestion(source_name: str, index_after_crawl: bool):
        raise ValueError("Unknown source: bad")

    monkeypatch.setattr("api.ingestion_routes.start_ingestion", fake_start_ingestion)
    resp = client.post("/api/ingestion/start", json={"source_name": "bad"})
    assert resp.status_code == 404
    assert "Unknown source" in resp.json()["detail"]


def test_list_runs_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.list_runs",
        lambda limit, source_name: [{"id": 1, "source_name": "hugo_love", "status": "completed"}],
    )
    resp = client.get("/api/ingestion/runs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["runs"][0]["id"] == 1


def test_get_run_404_when_missing(client, monkeypatch):
    monkeypatch.setattr("api.ingestion_routes.get_run", lambda run_id: None)
    resp = client.get("/api/ingestion/runs/999")
    assert resp.status_code == 404
    assert "Run not found" in resp.json()["detail"]


def test_get_run_errors_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.get_run_errors",
        lambda run_id, limit: [{"id": 1, "crawl_run_id": run_id, "error_type": "http_error"}],
    )
    resp = client.get("/api/ingestion/errors/10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == 10
    assert body["count"] == 1
    assert body["errors"][0]["error_type"] == "http_error"


def test_start_ingestion_batch_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.start_ingestion_batch",
        lambda source_names, only_active, index_after_crawl, stop_on_error: {
            "results": [{"source_name": "paul_graham_essays", "status": "ok"}],
            "count": 1,
        },
    )
    resp = client.post(
        "/api/ingestion/start-batch",
        json={"only_active": True, "index_after_crawl": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["source_name"] == "paul_graham_essays"


def test_get_sources_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.list_sources",
        lambda only_active: [{"name": "a16z_speedrun", "is_active": True}],
    )
    resp = client.get("/api/ingestion/sources?only_active=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["sources"][0]["name"] == "a16z_speedrun"


def test_onboard_source_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.onboard_source",
        lambda payload: {"name": payload["name"], "domain": payload["domain"], "is_active": True},
    )
    resp = client.post(
        "/api/ingestion/sources",
        json={
            "name": "new_source",
            "domain": "example.com",
            "start_urls": ["https://example.com/"],
            "allowed_paths": ["/"],
            "blocked_paths": [],
            "max_depth": 2,
            "max_pages": 100,
            "is_active": True,
            "metadata": {"topic": "startup"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "new_source"
    assert body["domain"] == "example.com"


def test_import_local_directory_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.import_local_directory",
        lambda directory, source_name, topic, recursive, index_after_import: {
            "source_name": source_name,
            "files_seen": 35,
            "files_imported": 35,
            "pages_indexed": 35,
            "total_chunks": 140,
        },
    )
    resp = client.post(
        "/api/ingestion/import/local",
        json={
            "directory": "data/startup_strategy_pack",
            "source_name": "startup_strategy_pack",
            "topic": "startup_strategy",
            "recursive": True,
            "index_after_import": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["files_seen"] == 35
    assert body["pages_indexed"] == 35


def test_get_ingestion_metrics_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.ingestion_metrics",
        lambda: {"total_sources": 3, "total_runs": 10},
    )
    resp = client.get("/api/ingestion/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["metrics"]["total_sources"] == 3


def test_get_ingestion_health_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.ingestion_health",
        lambda: {"status": "ok", "latest_run": {"id": 10}},
    )
    resp = client.get("/api/ingestion/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_ingestion_freshness_success(client, monkeypatch):
    monkeypatch.setattr(
        "api.ingestion_routes.source_freshness",
        lambda max_age_hours: {"max_age_hours": max_age_hours, "stale_count": 1, "sources": []},
    )
    resp = client.get("/api/ingestion/freshness?max_age_hours=48")
    assert resp.status_code == 200
    body = resp.json()
    assert body["max_age_hours"] == 48
    assert body["stale_count"] == 1
