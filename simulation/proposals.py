"""
Proposal and vote dataclasses with regex parsers.

Agents include structured [PROPOSAL] and [VOTE] blocks in their responses.
The extract_* functions parse these blocks into typed dataclasses.
"""

import re
import uuid
from dataclasses import dataclass


@dataclass
class Proposal:
    title: str
    description: str
    estimated_cost: float
    proposer: str  # agent name, e.g. "Product Agent"
    proposal_id: str = ""

    def __post_init__(self):
        if not self.proposal_id:
            self.proposal_id = uuid.uuid4().hex[:8]


@dataclass
class AgentVote:
    proposal_id: str
    agent: str  # voter's name
    vote: str  # "approve" | "reject" | "abstain"
    reasoning: str = ""


_PROPOSAL_PATTERN = re.compile(
    r"\[PROPOSAL\]\s*"
    r"Title:\s*(.+?)\s*"
    r"Cost:\s*\$?([\d,]+(?:\.\d{1,2})?)\s*"
    r"Description:\s*(.+?)\s*"
    r"\[/PROPOSAL\]",
    re.DOTALL | re.IGNORECASE,
)

_VOTE_PATTERN = re.compile(
    r"\[VOTE\]\s*"
    r"Proposal:\s*(\w+)\s*"
    r"Vote:\s*(approve|reject|abstain)\s*"
    r"(?:Reasoning:\s*(.+?)\s*)?"
    r"\[/VOTE\]",
    re.DOTALL | re.IGNORECASE,
)


def extract_proposal_from_response(content: str, proposer: str) -> Proposal | None:
    """
    Extract a Proposal from agent response text.
    Returns None if no [PROPOSAL] block found.
    """
    match = _PROPOSAL_PATTERN.search(content)
    if not match:
        return None

    title = match.group(1).strip()
    cost_str = match.group(2).replace(",", "")
    description = match.group(3).strip()

    return Proposal(
        title=title,
        description=description,
        estimated_cost=float(cost_str),
        proposer=proposer,
    )


def extract_vote_from_response(content: str, agent: str) -> AgentVote | None:
    """
    Extract an AgentVote from agent response text.
    Returns None if no [VOTE] block found.
    """
    match = _VOTE_PATTERN.search(content)
    if not match:
        return None

    return AgentVote(
        proposal_id=match.group(1).strip(),
        agent=agent,
        vote=match.group(2).strip().lower(),
        reasoning=(match.group(3) or "").strip(),
    )
