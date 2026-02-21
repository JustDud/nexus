"""Tests for FastAPI routes — uses TestClient, no live LLM/embedding calls."""

# conftest.py sets dummy API keys before this module loads.

import pytest

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAgentsListEndpoint:
    def test_list_agents(self, client):
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.json()

        expected_agents = {"advisor", "market", "product", "tech", "finance", "risk"}
        assert set(data.keys()) == expected_agents

    def test_each_agent_has_fields(self, client):
        resp = client.get("/api/agents")
        data = resp.json()

        for name, agent_info in data.items():
            assert "name" in agent_info, f"{name} missing 'name'"
            assert "role" in agent_info, f"{name} missing 'role'"
            assert "domain" in agent_info, f"{name} missing 'domain'"

    def test_agent_domains_match_keys(self, client):
        resp = client.get("/api/agents")
        data = resp.json()

        for key, agent_info in data.items():
            if key == "advisor":
                continue  # advisor has no domain filter
            assert agent_info["domain"] == key


class TestQueryEndpointValidation:
    def test_query_unknown_agent_returns_404(self, client):
        resp = client.post(
            "/api/agents/nonexistent/query",
            json={"question": "test"},
        )
        assert resp.status_code == 404
        assert "Unknown agent" in resp.json()["detail"]

    def test_query_direct_unknown_agent_returns_404(self, client):
        resp = client.post(
            "/api/agents/nonexistent/query-direct",
            json={"question": "test"},
        )
        assert resp.status_code == 404

    def test_query_missing_body_returns_422(self, client):
        resp = client.post("/api/agents/market/query")
        assert resp.status_code == 422

    def test_query_empty_question_accepted(self, client):
        """Empty string is valid input — the agent should handle it."""
        # This will fail at the API call level (no real key) but should
        # pass request validation
        resp = client.post(
            "/api/agents/market/query",
            json={"question": ""},
        )
        # Should not be 422 (validation error)
        assert resp.status_code != 422


class TestIngestEndpointValidation:
    def test_ingest_directory_missing_body(self, client):
        resp = client.post("/api/rag/ingest/directory")
        assert resp.status_code == 422

    def test_ingest_directory_nonexistent_path(self, client):
        resp = client.post(
            "/api/rag/ingest/directory",
            json={"directory": "/nonexistent/path", "domain": "test"},
        )
        assert resp.status_code == 404

    def test_ingest_text_missing_body(self, client):
        resp = client.post("/api/rag/ingest/text")
        assert resp.status_code == 422

    def test_search_missing_body(self, client):
        resp = client.post("/api/rag/search")
        assert resp.status_code == 422


class TestRequestModels:
    def test_query_with_context(self, client):
        """Context dict should be accepted without validation errors."""
        resp = client.post(
            "/api/agents/market/query",
            json={
                "question": "What is the market size?",
                "context": {"budget": 1000, "phase": "research"},
            },
        )
        # Should not be 422
        assert resp.status_code != 422

    def test_ingest_text_with_source_name(self, client):
        """Custom source_name should be accepted."""
        # This will fail at embedding level (no real API key) but should
        # not fail at validation
        resp = client.post(
            "/api/rag/ingest/text",
            json={
                "text": "Some content",
                "domain": "market",
                "source_name": "my_report",
            },
        )
        assert resp.status_code != 422

    def test_search_with_all_params(self, client):
        """All optional params should be accepted."""
        resp = client.post(
            "/api/rag/search",
            json={"query": "test", "domain": "market", "top_k": 3},
        )
        assert resp.status_code != 422
