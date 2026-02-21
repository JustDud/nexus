"""Proposal and vote data structures, plus extraction from agent responses."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class ProposalStatus(StrEnum):
    PROPOSED = "proposed"
    DEBATING = "debating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXECUTED = "executed"


@dataclass
class AgentVote:
    agent: str
    stance: str  # "support", "oppose", "conditional"
    reasoning: str = ""
    conditions: str = ""


@dataclass
class Proposal:
    id: str
    title: str
    description: str
    proposed_by: str
    estimated_cost: str
    category: str
    votes: list[AgentVote] = field(default_factory=list)
    status: ProposalStatus = ProposalStatus.PROPOSED

    @property
    def supporters(self) -> list[str]:
        return [v.agent for v in self.votes if v.stance == "support"]

    @property
    def opponents(self) -> list[str]:
        return [v.agent for v in self.votes if v.stance == "oppose"]

    def to_decision_card(self) -> dict:
        return {
            "proposal_id": self.id,
            "title": self.title,
            "proposed_by": self.proposed_by,
            "estimated_cost": self.estimated_cost,
            "category": self.category,
            "status": str(self.status),
            "supporters": [
                {"agent": v.agent, "reasoning": v.reasoning}
                for v in self.votes
                if v.stance == "support"
            ],
            "opponents": [
                {"agent": v.agent, "reasoning": v.reasoning}
                for v in self.votes
                if v.stance == "oppose"
            ],
            "conditions": [
                {"agent": v.agent, "reasoning": v.reasoning, "conditions": v.conditions}
                for v in self.votes
                if v.stance == "conditional"
            ],
        }


def _extract_marker(content: str, marker: str) -> str:
    """Extract value after a MARKER: prefix line."""
    pattern = rf"^{re.escape(marker)}:\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_proposal_from_response(content: str, agent_name: str) -> Proposal | None:
    """Extract a proposal from agent response text using PROPOSAL/COST/CATEGORY/REASON markers."""
    title = _extract_marker(content, "PROPOSAL")
    if not title:
        return None

    cost = _extract_marker(content, "COST") or "$0"
    category = _extract_marker(content, "CATEGORY") or "general"
    reason = _extract_marker(content, "REASON")

    return Proposal(
        id=uuid.uuid4().hex[:8],
        title=title,
        description=reason,
        proposed_by=agent_name,
        estimated_cost=cost,
        category=category,
    )


def extract_vote_from_response(content: str, agent_name: str) -> AgentVote | None:
    """Extract a vote from agent response text using VOTE/REASONING/CONDITIONS markers."""
    stance_raw = _extract_marker(content, "VOTE")
    if not stance_raw:
        return None

    stance = stance_raw.lower().strip()
    reasoning = _extract_marker(content, "REASONING")
    conditions = _extract_marker(content, "CONDITIONS")

    return AgentVote(
        agent=agent_name,
        stance=stance,
        reasoning=reasoning,
        conditions=conditions,
    )
