"""Tests for api/simulation_routes.py — all 6 simulation endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from simulation.session import _sessions, get_session


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Ensure a clean session store for each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture(autouse=True)
def _no_orchestrator():
    """Prevent the orchestrator from running during API tests."""
    with patch("api.simulation_routes._run_simulation", new_callable=AsyncMock):
        yield


@pytest.fixture
def started_session(client):
    """Create a session and return its ID."""
    resp = client.post(
        "/api/simulation/start",
        json={"idea": "AI pet grooming marketplace", "budget": 50000.0},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


# ---------------------------------------------------------------------------
# POST /api/simulation/start
# ---------------------------------------------------------------------------


class TestStartSimulation:
    def test_start_returns_session_id(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "AI tutoring app", "budget": 10000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["idea"] == "AI tutoring app"
        assert data["budget"] == 10000

    def test_start_returns_running_status(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "Test idea", "budget": 1000},
        )
        assert resp.json()["status"] == "running"

    def test_start_returns_created_at(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "Test idea", "budget": 1000},
        )
        assert "created_at" in resp.json()

    def test_start_missing_idea_returns_422(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"budget": 1000},
        )
        assert resp.status_code == 422

    def test_start_missing_budget_returns_422(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "AI app"},
        )
        assert resp.status_code == 422

    def test_start_zero_budget_returns_422(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "AI app", "budget": 0},
        )
        assert resp.status_code == 422

    def test_start_negative_budget_returns_422(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "AI app", "budget": -100},
        )
        assert resp.status_code == 422

    def test_start_empty_idea_returns_422(self, client):
        resp = client.post(
            "/api/simulation/start",
            json={"idea": "", "budget": 1000},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/simulation/sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    def test_list_empty(self, client):
        resp = client.get("/api/simulation/sessions")
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_list_after_start(self, client, started_session):
        resp = client.get("/api/simulation/sessions")
        assert resp.status_code == 200
        sessions = resp.json()["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == started_session

    def test_list_multiple_sessions(self, client):
        client.post("/api/simulation/start", json={"idea": "A", "budget": 100})
        client.post("/api/simulation/start", json={"idea": "B", "budget": 200})
        resp = client.get("/api/simulation/sessions")
        assert len(resp.json()["sessions"]) == 2


# ---------------------------------------------------------------------------
# GET /api/simulation/sessions/{id}
# ---------------------------------------------------------------------------


class TestGetSession:
    def test_get_existing_session(self, client, started_session):
        resp = client.get(f"/api/simulation/sessions/{started_session}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == started_session
        assert data["idea"] == "AI pet grooming marketplace"
        assert data["budget"] == 50000.0
        assert data["status"] == "running"

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/simulation/sessions/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_get_includes_event_count(self, client, started_session):
        resp = client.get(f"/api/simulation/sessions/{started_session}")
        data = resp.json()
        assert "event_count" in data
        # Orchestrator is mocked in tests, so no events emitted yet
        assert data["event_count"] == 1


# ---------------------------------------------------------------------------
# POST /api/simulation/sessions/{id}/decide
# ---------------------------------------------------------------------------


class TestDecision:
    def test_decide_nonexistent_session_returns_404(self, client):
        resp = client.post(
            "/api/simulation/sessions/nonexistent/decide",
            json={"proposal_id": "abc", "approved": True},
        )
        assert resp.status_code == 404

    def test_decide_on_running_session_returns_400(self, client, started_session):
        resp = client.post(
            f"/api/simulation/sessions/{started_session}/decide",
            json={"proposal_id": "abc", "approved": True},
        )
        assert resp.status_code == 400
        assert "paused" in resp.json()["detail"].lower()

    def test_decide_missing_body_returns_422(self, client, started_session):
        resp = client.post(f"/api/simulation/sessions/{started_session}/decide")
        assert resp.status_code == 422

    def test_decide_valid(self, client, started_session):
        # Manually set session to paused
        session = get_session(started_session)
        session.status = "paused"

        resp = client.post(
            f"/api/simulation/sessions/{started_session}/decide",
            json={"proposal_id": "prop123", "approved": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["proposal_id"] == "prop123"
        assert data["approved"] is True
        assert data["status"] == "running"

    def test_decide_reject(self, client, started_session):
        session = get_session(started_session)
        session.status = "paused"

        resp = client.post(
            f"/api/simulation/sessions/{started_session}/decide",
            json={"proposal_id": "prop456", "approved": False},
        )
        assert resp.status_code == 200
        assert resp.json()["approved"] is False


# ---------------------------------------------------------------------------
# GET /api/simulation/sessions/{id}/report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_nonexistent_returns_404(self, client):
        resp = client.get("/api/simulation/sessions/nonexistent/report")
        assert resp.status_code == 404

    def test_report_on_existing_session(self, client, started_session):
        resp = client.get(f"/api/simulation/sessions/{started_session}/report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == started_session
        assert data["idea"] == "AI pet grooming marketplace"
        assert data["initial_budget"] == 50000.0
        assert "summary" in data
        assert "proposals" in data
        assert "decisions" in data
        assert "key_events" in data

    def test_report_captures_start_event(self, client, started_session):
        resp = client.get(f"/api/simulation/sessions/{started_session}/report")
        data = resp.json()
        # The start endpoint emits SIMULATION_STARTED, which is a key event
        assert len(data["key_events"]) == 1
        assert data["key_events"][0]["type"] == "simulation_started"


# ---------------------------------------------------------------------------
# GET /api/simulation/sessions/{id}/events (SSE)
# ---------------------------------------------------------------------------


class TestSSEEvents:
    def test_sse_nonexistent_session_returns_404(self, client):
        resp = client.get("/api/simulation/sessions/nonexistent/events")
        assert resp.status_code == 404


class TestEventBusUnit:
    """Unit tests for EventBus and SSE formatting (no HTTP layer)."""

    def test_event_to_sse_format(self):
        from simulation.events import EventType, SimulationEvent

        event = SimulationEvent(
            event_type=EventType.AGENT_RESPONSE,
            data={"agent": "market", "content": "hello"},
        )
        sse = event.to_sse()
        assert sse.startswith("event: agent_response\n")
        assert "data: " in sse
        assert sse.endswith("\n\n")

    def test_event_bus_emit_and_history(self):
        import asyncio

        from simulation.events import EventBus, EventType, SimulationEvent

        bus = EventBus()
        event = SimulationEvent(event_type=EventType.ROUND_STARTED, data={"round": 1})

        loop = asyncio.new_event_loop()
        loop.run_until_complete(bus.emit(event))
        loop.close()

        assert len(bus.history) == 1
        assert bus.history[0].event_type == EventType.ROUND_STARTED

    def test_event_bus_subscribe_receives_events(self):
        import asyncio

        from simulation.events import EventBus, EventType, SimulationEvent

        bus = EventBus()
        sub_id, queue = bus.subscribe()

        event = SimulationEvent(
            event_type=EventType.SIMULATION_COMPLETED, data={"done": True}
        )

        loop = asyncio.new_event_loop()
        loop.run_until_complete(bus.emit(event))
        received = loop.run_until_complete(queue.get())
        loop.close()

        assert received.event_type == EventType.SIMULATION_COMPLETED
        assert received.data == {"done": True}

        bus.unsubscribe(sub_id)

    def test_event_bus_unsubscribe(self):
        import asyncio

        from simulation.events import EventBus, EventType, SimulationEvent

        bus = EventBus()
        sub_id, queue = bus.subscribe()
        bus.unsubscribe(sub_id)

        event = SimulationEvent(event_type=EventType.ERROR, data={})

        loop = asyncio.new_event_loop()
        loop.run_until_complete(bus.emit(event))
        loop.close()

        assert queue.empty()  # unsubscribed, should not receive
