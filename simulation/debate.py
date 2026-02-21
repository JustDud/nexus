"""Debate manager — runs structured multi-round debates between agents."""

from __future__ import annotations

import asyncio

from agents.base import BaseAgent
from simulation.events import (
    AGENT_SPEAKING,
    AGENT_THINKING,
    CONSENSUS_REACHED,
    DEBATE_ROUND_COMPLETE,
    PROPOSAL_ESCALATED,
    VOTE_CAST,
    EventBus,
)
from simulation.prompts import debate_response_prompt
from simulation.proposals import (
    Proposal,
    ProposalStatus,
    extract_proposal_from_response,
    extract_vote_from_response,
)
from simulation.state import Phase, SimulationState

# All agents debate each round in parallel
TURN_ORDER = ["product", "tech", "finance", "risk", "market"]

# Map backend agent keys to frontend agent IDs
_FRONTEND_ID = {
    "market": "product",
    "product": "product",
    "tech": "tech",
    "finance": "finance",
    "risk": "ops",
}


class DebateManager:
    """Runs a structured debate between agents on proposals."""

    def __init__(
        self,
        agents: dict[str, BaseAgent],
        state: SimulationState,
        event_bus: EventBus,
    ) -> None:
        self.agents = agents
        self.state = state
        self.event_bus = event_bus

    async def _run_agent_turn(
        self, agent_key: str, round_num: int, topic: str,
    ):
        """Run a single agent's debate turn. Safe for parallel execution."""
        agent = self.agents[agent_key]
        agent_name = agent.config.name
        fid = _FRONTEND_ID.get(agent_key, "tech")

        await self.event_bus.emit(AGENT_THINKING, {
            "agent_id": fid,
            "agent_name": agent_name,
            "round": round_num,
            "task": f"Debating round {round_num}",
        })

        prompt = debate_response_prompt(agent_name, topic)
        context = self.state.get_context_dict()
        response = await agent.query_without_rag(prompt, context=context)

        self.state.add_message(
            agent=response.agent,
            role=response.role,
            content=response.content,
            phase=Phase.DEBATE,
            round_number=round_num,
            citations=response.citations,
        )

        await self.event_bus.emit(AGENT_SPEAKING, {
            "agent_id": fid,
            "agent_name": agent_name,
            "round": round_num,
            "content": response.content,
        })

        return agent_key, agent_name, fid, response

    async def run_debate(
        self,
        topic: str,
        initial_proposals: list[Proposal],
        max_rounds: int = 3,
    ) -> list[Proposal]:
        """Run a multi-round debate. All agents speak in parallel each round."""
        proposals = list(initial_proposals)
        for p in proposals:
            p.status = ProposalStatus.DEBATING

        for round_num in range(1, max_rounds + 1):
            self.state.current_round = round_num

            # All agents debate simultaneously
            results = await asyncio.gather(
                *(self._run_agent_turn(ak, round_num, topic) for ak in TURN_ORDER)
            )

            # Process all results after the parallel batch
            for agent_key, agent_name, fid, response in results:
                new_proposal = extract_proposal_from_response(response.content, agent_name)
                if new_proposal:
                    new_proposal.status = ProposalStatus.DEBATING
                    proposals.append(new_proposal)

                vote = extract_vote_from_response(response.content, agent_name)
                if vote:
                    for p in proposals:
                        p.votes = [v for v in p.votes if v.agent != agent_name]
                        p.votes.append(vote)
                    await self.event_bus.emit(VOTE_CAST, {
                        "agent_id": fid,
                        "agent_name": agent_name,
                        "stance": vote.stance,
                        "round": round_num,
                    })

            await self.event_bus.emit(DEBATE_ROUND_COMPLETE, {"round": round_num})

            if self._check_consensus(proposals):
                await self.event_bus.emit(CONSENSUS_REACHED, {
                    "round": round_num,
                    "proposals": [p.title for p in proposals],
                })
                break

        # After all rounds: mark unresolved proposals as escalated
        for p in proposals:
            if p.status == ProposalStatus.DEBATING:
                if self._has_consensus(p):
                    if all(v.stance == "support" for v in p.votes):
                        p.status = ProposalStatus.APPROVED
                    elif all(v.stance == "oppose" for v in p.votes):
                        p.status = ProposalStatus.REJECTED
                    else:
                        p.status = ProposalStatus.ESCALATED
                        await self.event_bus.emit(PROPOSAL_ESCALATED, {
                            "proposal_id": p.id,
                            "title": p.title,
                        })
                else:
                    p.status = ProposalStatus.ESCALATED
                    await self.event_bus.emit(PROPOSAL_ESCALATED, {
                        "proposal_id": p.id,
                        "title": p.title,
                    })

        return proposals

    def _check_consensus(self, proposals: list[Proposal]) -> bool:
        """Check if all proposals have unanimous votes."""
        return all(self._has_consensus(p) for p in proposals)

    @staticmethod
    def _has_consensus(proposal: Proposal) -> bool:
        """A proposal has consensus if it has votes and all stances agree."""
        if not proposal.votes:
            return False
        stances = {v.stance for v in proposal.votes}
        return len(stances) == 1
