"""Tests for simulation.proposals extraction functions."""

from simulation.proposals import (
    AgentVote,
    Proposal,
    ProposalStatus,
    extract_proposal_from_response,
    extract_vote_from_response,
)


# --- Proposal extraction ---


def test_extract_proposal_all_markers():
    content = (
        "I recommend we act on this.\n"
        "PROPOSAL: Build MVP landing page\n"
        "COST: $500\n"
        "CATEGORY: marketing\n"
        "REASON: We need to validate demand before building the full product."
    )
    p = extract_proposal_from_response(content, "Strategist")
    assert p is not None
    assert p.title == "Build MVP landing page"
    assert p.estimated_cost == "$500"
    assert p.category == "marketing"
    assert p.description == "We need to validate demand before building the full product."
    assert p.proposed_by == "Strategist"
    assert p.status == ProposalStatus.PROPOSED
    assert len(p.id) == 8


def test_extract_proposal_missing_markers_returns_none():
    content = "I think we should build a landing page but I'm not sure about the cost."
    assert extract_proposal_from_response(content, "Strategist") is None


def test_extract_proposal_partial_markers():
    content = "PROPOSAL: Hire a designer\nSome other text without cost or category."
    p = extract_proposal_from_response(content, "Ops")
    assert p is not None
    assert p.title == "Hire a designer"
    assert p.estimated_cost == "$0"
    assert p.category == "general"
    assert p.description == ""


def test_extract_proposal_cost_hundreds():
    content = "PROPOSAL: Buy domain\nCOST: $100\nCATEGORY: infrastructure"
    p = extract_proposal_from_response(content, "CTO")
    assert p is not None
    assert p.estimated_cost == "$100"


def test_extract_proposal_cost_with_comma():
    content = "PROPOSAL: Run ad campaign\nCOST: $1,000\nCATEGORY: marketing"
    p = extract_proposal_from_response(content, "CMO")
    assert p is not None
    assert p.estimated_cost == "$1,000"


def test_extract_proposal_cost_with_decimals():
    content = "PROPOSAL: Buy coffee\nCOST: $100.00\nCATEGORY: morale"
    p = extract_proposal_from_response(content, "Ops")
    assert p is not None
    assert p.estimated_cost == "$100.00"


# --- Vote extraction ---


def test_extract_vote_support():
    content = "VOTE: SUPPORT\nREASONING: This aligns with our strategy."
    v = extract_vote_from_response(content, "CFO")
    assert v is not None
    assert v.stance == "support"
    assert v.reasoning == "This aligns with our strategy."
    assert v.conditions == ""
    assert v.agent == "CFO"


def test_extract_vote_oppose():
    content = "VOTE: OPPOSE\nREASONING: Too expensive for current runway."
    v = extract_vote_from_response(content, "CFO")
    assert v is not None
    assert v.stance == "oppose"
    assert v.reasoning == "Too expensive for current runway."


def test_extract_vote_conditional():
    content = (
        "VOTE: CONDITIONAL\n"
        "REASONING: Good idea but needs budget cap.\n"
        "CONDITIONS: Must stay under $500 total."
    )
    v = extract_vote_from_response(content, "Strategist")
    assert v is not None
    assert v.stance == "conditional"
    assert v.reasoning == "Good idea but needs budget cap."
    assert v.conditions == "Must stay under $500 total."


def test_extract_vote_missing_markers_returns_none():
    content = "I think this is a great idea and I support it fully."
    assert extract_vote_from_response(content, "CTO") is None


def test_extract_vote_without_reasoning():
    content = "VOTE: SUPPORT"
    v = extract_vote_from_response(content, "CMO")
    assert v is not None
    assert v.stance == "support"
    assert v.reasoning == ""


# --- Proposal dataclass ---


def test_proposal_supporters_and_opponents():
    p = Proposal(
        id="abc12345",
        title="Test",
        description="desc",
        proposed_by="A",
        estimated_cost="$100",
        category="test",
        votes=[
            AgentVote(agent="B", stance="support", reasoning="good"),
            AgentVote(agent="C", stance="oppose", reasoning="bad"),
            AgentVote(agent="D", stance="support", reasoning="great"),
            AgentVote(agent="E", stance="conditional", reasoning="maybe", conditions="if cheap"),
        ],
    )
    assert p.supporters == ["B", "D"]
    assert p.opponents == ["C"]


def test_proposal_to_decision_card():
    p = Proposal(
        id="card0001",
        title="Launch beta",
        description="Release to early users",
        proposed_by="Strategist",
        estimated_cost="$2,000",
        category="product",
        votes=[
            AgentVote(agent="CTO", stance="support", reasoning="Ready to ship"),
            AgentVote(agent="CFO", stance="oppose", reasoning="Over budget"),
            AgentVote(agent="CMO", stance="conditional", reasoning="Need landing page", conditions="Landing page first"),
        ],
        status=ProposalStatus.DEBATING,
    )
    card = p.to_decision_card()
    assert card["proposal_id"] == "card0001"
    assert card["title"] == "Launch beta"
    assert card["proposed_by"] == "Strategist"
    assert card["estimated_cost"] == "$2,000"
    assert card["category"] == "product"
    assert card["status"] == "debating"
    assert len(card["supporters"]) == 1
    assert card["supporters"][0]["agent"] == "CTO"
    assert len(card["opponents"]) == 1
    assert card["opponents"][0]["agent"] == "CFO"
    assert len(card["conditions"]) == 1
    assert card["conditions"][0]["conditions"] == "Landing page first"
