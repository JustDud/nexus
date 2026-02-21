"""Tests for translate_event and orchestrator helpers."""

import pytest

from simulation.events import EventType, SimulationEvent
from api.ws_routes import translate_event


class TestTranslateEvent:
    def test_agent_thinking(self):
        event = SimulationEvent(
            event_type=EventType.AGENT_THINKING,
            data={"agent_id": "tech", "agent_name": "tech"},
        )
        msgs = translate_event(event)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["type"] == "agent_thinking"
        assert msgs[0]["agentId"] == "tech"
        assert isinstance(msgs[0]["fragments"], list)

    def test_agent_response(self):
        event = SimulationEvent(
            event_type=EventType.AGENT_RESPONSE,
            data={
                "agent_id": "product",
                "agent_name": "product",
                "content": "We should build a mobile app. Focus on UX. Target millennials.",
            },
        )
        msgs = translate_event(event)
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["type"] == "agent_thinking"
        assert msgs[0]["agentId"] == "product"
        assert msgs[1]["type"] == "agent_acting"
        assert msgs[1]["agentId"] == "product"

    def test_budget_updated(self):
        event = SimulationEvent(
            event_type=EventType.BUDGET_UPDATED,
            data={
                "agent_id": "tech",
                "description": "AWS hosting",
                "amount": 500,
                "approved": True,
                "spent": 500,
                "total": 10000,
            },
        )
        msgs = translate_event(event)
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["type"] == "transaction"
        assert msgs[0]["status"] == "approved"
        assert msgs[0]["amount"] == 500
        assert msgs[1]["type"] == "budget_update"
        assert msgs[1]["spent"] == 500
        assert msgs[1]["total"] == 10000

    def test_budget_updated_blocked(self):
        event = SimulationEvent(
            event_type=EventType.BUDGET_UPDATED,
            data={
                "agent_id": "tech",
                "description": "Expensive tool",
                "amount": 99999,
                "approved": False,
                "spent": 0,
                "total": 1000,
            },
        )
        msgs = translate_event(event)
        assert msgs[0]["status"] == "blocked"

    def test_round_completed_researching(self):
        event = SimulationEvent(
            event_type=EventType.ROUND_COMPLETED,
            data={"round": "researching"},
        )
        msgs = translate_event(event)
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["type"] == "stage_change"
        assert msgs[0]["stage"] == "planning"

    def test_round_completed_planning(self):
        event = SimulationEvent(
            event_type=EventType.ROUND_COMPLETED,
            data={"round": "planning"},
        )
        msgs = translate_event(event)
        assert msgs[0]["stage"] == "building"

    def test_round_completed_building(self):
        event = SimulationEvent(
            event_type=EventType.ROUND_COMPLETED,
            data={"round": "building"},
        )
        msgs = translate_event(event)
        assert msgs[0]["stage"] == "deploying"

    def test_round_completed_deploying(self):
        event = SimulationEvent(
            event_type=EventType.ROUND_COMPLETED,
            data={"round": "deploying"},
        )
        msgs = translate_event(event)
        assert msgs[0]["stage"] == "complete"

    def test_simulation_completed(self):
        event = SimulationEvent(
            event_type=EventType.SIMULATION_COMPLETED,
            data={"spent": 5000, "remaining": 5000},
        )
        msgs = translate_event(event)
        assert msgs is not None
        # 4 agent_complete messages + 1 stage_change
        assert len(msgs) == 5
        agent_ids = [m["agentId"] for m in msgs if m["type"] == "agent_complete"]
        assert set(agent_ids) == {"product", "tech", "ops", "finance"}
        assert msgs[-1]["type"] == "stage_change"
        assert msgs[-1]["stage"] == "complete"

    def test_unknown_event_returns_none(self):
        event = SimulationEvent(
            event_type=EventType.DEBATE_STARTED,
            data={"topic": "something"},
        )
        assert translate_event(event) is None

    def test_round_started_returns_none(self):
        event = SimulationEvent(
            event_type=EventType.ROUND_STARTED,
            data={"round": "researching"},
        )
        assert translate_event(event) is None

    def test_agent_response_long_content_truncated(self):
        long_content = "A" * 200
        event = SimulationEvent(
            event_type=EventType.AGENT_RESPONSE,
            data={"agent_id": "tech", "agent_name": "tech", "content": long_content},
        )
        msgs = translate_event(event)
        assert len(msgs[1]["action"]) < 200

    def test_agent_response_empty_content(self):
        event = SimulationEvent(
            event_type=EventType.AGENT_RESPONSE,
            data={"agent_id": "ops", "agent_name": "risk", "content": ""},
        )
        msgs = translate_event(event)
        assert msgs[0]["fragments"] == ["Processing..."]
