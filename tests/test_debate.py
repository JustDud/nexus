"""Tests for DebateManager — consensus detection, turn order, escalation."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.base import AgentConfig, AgentResponse, BaseAgent
from simulation.debate import TURN_ORDER, DebateManager
from simulation.events import EventBus
from simulation.proposals import AgentVote, Proposal, ProposalStatus
from simulation.state import Phase, SimulationState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state() -> SimulationState:
    state = SimulationState()
    state.initialize("AI dog walker", 50_000)
    state.phase = Phase.DEBATE
    return state


def _make_proposal(**overrides) -> Proposal:
    defaults = {
        "id": "test0001",
        "title": "Test proposal",
        "description": "A test",
        "proposed_by": "Product Agent",
        "estimated_cost": "$1,000",
        "category": "engineering",
    }
    defaults.update(overrides)
    return Proposal(**defaults)


def _make_agents(response_content: str = "I agree.\nVOTE: SUPPORT\nREASONING: Looks good.") -> dict[str, AsyncMock]:
    """Create mock agents keyed by TURN_ORDER names."""
    agents = {}
    for key in TURN_ORDER:
        mock_agent = AsyncMock(spec=BaseAgent)
        mock_agent.config = AgentConfig(
            name=f"{key.title()} Agent",
            role=f"{key} role",
            domain=key,
            system_prompt="test",
        )
        mock_agent.query_without_rag.return_value = AgentResponse(
            agent=f"{key.title()} Agent",
            role=f"{key} role",
            content=response_content,
        )
        agents[key] = mock_agent
    return agents


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConsensusDetection:
    def test_unanimous_support_is_consensus(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents()
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal(votes=[
            AgentVote(agent="A", stance="support", reasoning="yes"),
            AgentVote(agent="B", stance="support", reasoning="yes"),
            AgentVote(agent="C", stance="support", reasoning="yes"),
        ])
        assert dm._has_consensus(proposal) is True
        assert dm._check_consensus([proposal]) is True

    def test_unanimous_oppose_is_consensus(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents()
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal(votes=[
            AgentVote(agent="A", stance="oppose", reasoning="no"),
            AgentVote(agent="B", stance="oppose", reasoning="no"),
        ])
        assert dm._has_consensus(proposal) is True

    def test_mixed_votes_no_consensus(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents()
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal(votes=[
            AgentVote(agent="A", stance="support", reasoning="yes"),
            AgentVote(agent="B", stance="oppose", reasoning="no"),
        ])
        assert dm._has_consensus(proposal) is False
        assert dm._check_consensus([proposal]) is False

    def test_no_votes_no_consensus(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents()
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal()
        assert dm._has_consensus(proposal) is False

    def test_all_proposals_must_have_consensus(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents()
        dm = DebateManager(agents, state, bus)

        p1 = _make_proposal(id="p1", votes=[
            AgentVote(agent="A", stance="support", reasoning="yes"),
        ])
        p2 = _make_proposal(id="p2", votes=[
            AgentVote(agent="A", stance="support", reasoning="yes"),
            AgentVote(agent="B", stance="oppose", reasoning="no"),
        ])
        assert dm._check_consensus([p1, p2]) is False


class TestTurnOrder:
    @pytest.mark.asyncio
    async def test_agents_called_in_order(self):
        state = _make_state()
        bus = EventBus()
        # All agents vote SUPPORT → consensus after round 1
        agents = _make_agents("I agree.\nVOTE: SUPPORT\nREASONING: Looks good.")
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal()
        await dm.run_debate("test topic", [proposal], max_rounds=1)

        # Verify each agent was called exactly once (1 round)
        call_order = []
        for key in TURN_ORDER:
            agents[key].query_without_rag.assert_called_once()
            call_order.append(key)

        assert call_order == ["product", "tech", "finance", "risk", "market"]

    @pytest.mark.asyncio
    async def test_messages_recorded_in_state(self):
        state = _make_state()
        bus = EventBus()
        agents = _make_agents("I agree.\nVOTE: SUPPORT\nREASONING: Looks good.")
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal()
        await dm.run_debate("test topic", [proposal], max_rounds=1)

        debate_msgs = [m for m in state.conversation if m.phase == Phase.DEBATE]
        assert len(debate_msgs) == 5  # one per agent
        assert debate_msgs[0].agent == "Product Agent"
        assert debate_msgs[4].agent == "Market Agent"


class TestMaxRoundsEscalation:
    @pytest.mark.asyncio
    async def test_escalation_after_max_rounds(self):
        """Mixed votes after max rounds → proposals escalated (status PROPOSED)."""
        state = _make_state()
        bus = EventBus()

        # Create agents with alternating support/oppose by agent
        agents = {}
        for i, key in enumerate(TURN_ORDER):
            mock_agent = AsyncMock(spec=BaseAgent)
            mock_agent.config = AgentConfig(
                name=f"{key.title()} Agent", role=f"{key} role",
                domain=key, system_prompt="test",
            )
            stance = "SUPPORT" if i % 2 == 0 else "OPPOSE"
            mock_agent.query_without_rag.return_value = AgentResponse(
                agent=f"{key.title()} Agent",
                role=f"{key} role",
                content=f"My take.\nVOTE: {stance}\nREASONING: Because.",
            )
            agents[key] = mock_agent

        dm = DebateManager(agents, state, bus)
        proposal = _make_proposal()
        results = await dm.run_debate("test topic", [proposal], max_rounds=2)

        # Should have run 2 rounds (max), no consensus
        assert len(results) == 1
        # Mixed votes → escalated back to PROPOSED
        assert results[0].status == ProposalStatus.PROPOSED

    @pytest.mark.asyncio
    async def test_early_stop_on_consensus(self):
        """If all agents agree in round 1, should not run round 2."""
        state = _make_state()
        bus = EventBus()
        agents = _make_agents("Agreed.\nVOTE: SUPPORT\nREASONING: Good.")
        dm = DebateManager(agents, state, bus)

        proposal = _make_proposal()
        results = await dm.run_debate("test topic", [proposal], max_rounds=3)

        # Only 1 round of messages (5 agents × 1 round)
        debate_msgs = [m for m in state.conversation if m.phase == Phase.DEBATE]
        assert len(debate_msgs) == 5
        assert results[0].status == ProposalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_escalation_emits_events(self):
        state = _make_state()
        bus = EventBus()
        events_received = []

        async def capture(event_type, data):
            events_received.append(event_type)

        bus.on("proposal_escalated", capture)

        # Mixed votes → no consensus
        agents = {}
        for i, key in enumerate(TURN_ORDER):
            mock_agent = AsyncMock(spec=BaseAgent)
            mock_agent.config = AgentConfig(
                name=f"{key.title()} Agent", role=f"{key} role",
                domain=key, system_prompt="test",
            )
            stance = "SUPPORT" if i == 0 else "OPPOSE"
            mock_agent.query_without_rag.return_value = AgentResponse(
                agent=f"{key.title()} Agent",
                role=f"{key} role",
                content=f"My view.\nVOTE: {stance}\nREASONING: Because.",
            )
            agents[key] = mock_agent

        dm = DebateManager(agents, state, bus)
        proposal = _make_proposal()
        await dm.run_debate("test topic", [proposal], max_rounds=1)

        assert "proposal_escalated" in events_received
