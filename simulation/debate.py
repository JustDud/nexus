"""Debate manager — runs structured multi-round debates between agents."""

from __future__ import annotations

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
    AgentVote,
    Proposal,
    ProposalStatus,
    extract_proposal_from_response,
    extract_vote_from_response,
)
from simulation.state import Phase, SimulationState

# Fixed turn order for each debate round
TURN_ORDER = ["product", "tech", "finance", "risk", "market"]


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

    async def run_debate(
        self,
        topic: str,
        initial_proposals: list[Proposal],
        max_rounds: int = 3,
    ) -> list[Proposal]:
        """Run a multi-round debate. Returns proposals with final votes/statuses."""
        proposals = list(initial_proposals)
        for p in proposals:
            p.status = ProposalStatus.DEBATING

        for round_num in range(1, max_rounds + 1):
            self.state.current_round = round_num

            for agent_key in TURN_ORDER:
                agent = self.agents[agent_key]
                agent_name = agent.config.name

                await self.event_bus.emit(AGENT_THINKING, {
                    "agent": agent_name,
                    "round": round_num,
                })

                prior = self._format_prior_messages()
                prompt = debate_response_prompt(agent_name, prior, topic)
                context = self.state.get_context_dict()

                response = await agent.query_without_rag(prompt, context=context)

                # Record message in state
                self.state.add_message(
                    agent=response.agent,
                    role=response.role,
                    content=response.content,
                    phase=Phase.DEBATE,
                    round_number=round_num,
                    citations=response.citations,
                )

                await self.event_bus.emit(AGENT_SPEAKING, {
                    "agent": agent_name,
                    "round": round_num,
                    "content": response.content,
                })

                # Extract new proposals from response
                new_proposal = extract_proposal_from_response(response.content, agent_name)
                if new_proposal:
                    new_proposal.status = ProposalStatus.DEBATING
                    proposals.append(new_proposal)

                # Extract votes and attach to matching proposals
                vote = extract_vote_from_response(response.content, agent_name)
                if vote:
                    for p in proposals:
                        # Remove previous vote by this agent, then add new one
                        p.votes = [v for v in p.votes if v.agent != agent_name]
                        p.votes.append(vote)
                    await self.event_bus.emit(VOTE_CAST, {
                        "agent": agent_name,
                        "stance": vote.stance,
                        "round": round_num,
                    })

            await self.event_bus.emit(DEBATE_ROUND_COMPLETE, {"round": round_num})

            # Check for consensus after each round
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
                    # Mixed votes — escalate to CEO
                    p.status = ProposalStatus.ESCALATED
                    await self.event_bus.emit(PROPOSAL_ESCALATED, {
                        "proposal_id": p.id,
                        "title": p.title,
                    })

        return proposals

    def _format_prior_messages(self) -> str:
        """Format debate messages for inclusion in prompts."""
        debate_msgs = [
            m for m in self.state.conversation if m.phase == Phase.DEBATE
        ]
        if not debate_msgs:
            return "(No prior debate messages.)"
        lines = []
        for m in debate_msgs:
            lines.append(f"[Round {m.round_number}] {m.agent} ({m.role}):\n{m.content}\n")
        return "\n".join(lines)

    def _get_debate_history(self) -> list[dict]:
        """Return debate messages as a list of dicts."""
        return [
            {
                "agent": m.agent,
                "role": m.role,
                "content": m.content,
                "round": m.round_number,
            }
            for m in self.state.conversation
            if m.phase == Phase.DEBATE
        ]

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
