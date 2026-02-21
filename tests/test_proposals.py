"""Tests for simulation/proposals.py — Proposal, AgentVote, and regex parsers."""

import pytest

from simulation.proposals import (
    AgentVote,
    Proposal,
    extract_proposal_from_response,
    extract_vote_from_response,
)


# ---------------------------------------------------------------------------
# Proposal dataclass
# ---------------------------------------------------------------------------


class TestProposalDataclass:
    def test_proposal_fields(self):
        p = Proposal(
            title="Auth module",
            description="OAuth2 login",
            estimated_cost=2500.0,
            proposer="Product Agent",
        )
        assert p.title == "Auth module"
        assert p.description == "OAuth2 login"
        assert p.estimated_cost == 2500.0
        assert p.proposer == "Product Agent"

    def test_proposal_gets_auto_id(self):
        p = Proposal(
            title="X", description="Y", estimated_cost=0, proposer="Z"
        )
        assert p.proposal_id
        assert len(p.proposal_id) == 8

    def test_proposal_custom_id(self):
        p = Proposal(
            title="X",
            description="Y",
            estimated_cost=0,
            proposer="Z",
            proposal_id="custom123",
        )
        assert p.proposal_id == "custom123"

    def test_two_proposals_have_different_ids(self):
        p1 = Proposal(title="A", description="B", estimated_cost=0, proposer="C")
        p2 = Proposal(title="A", description="B", estimated_cost=0, proposer="C")
        assert p1.proposal_id != p2.proposal_id


# ---------------------------------------------------------------------------
# AgentVote dataclass
# ---------------------------------------------------------------------------


class TestAgentVoteDataclass:
    def test_vote_fields(self):
        v = AgentVote(
            proposal_id="abc123",
            agent="Finance Agent",
            vote="reject",
            reasoning="Over budget",
        )
        assert v.proposal_id == "abc123"
        assert v.agent == "Finance Agent"
        assert v.vote == "reject"
        assert v.reasoning == "Over budget"

    def test_vote_default_reasoning(self):
        v = AgentVote(proposal_id="x", agent="y", vote="approve")
        assert v.reasoning == ""


# ---------------------------------------------------------------------------
# extract_proposal_from_response
# ---------------------------------------------------------------------------


class TestExtractProposal:
    def test_valid_proposal(self):
        content = (
            "Here is my analysis.\n\n"
            "[PROPOSAL]\n"
            "Title: Build user auth module\n"
            "Cost: $2500\n"
            "Description: Implement OAuth2 with Google login.\n"
            "[/PROPOSAL]\n\n"
            "That's my recommendation."
        )
        p = extract_proposal_from_response(content, "Product Agent")
        assert p is not None
        assert p.title == "Build user auth module"
        assert p.estimated_cost == 2500.0
        assert p.description == "Implement OAuth2 with Google login."
        assert p.proposer == "Product Agent"
        assert p.proposal_id  # auto-generated

    def test_cost_with_commas(self):
        content = (
            "[PROPOSAL]\n"
            "Title: Enterprise plan\n"
            "Cost: $12,500\n"
            "Description: Full suite.\n"
            "[/PROPOSAL]"
        )
        p = extract_proposal_from_response(content, "Market Agent")
        assert p is not None
        assert p.estimated_cost == 12500.0

    def test_cost_with_decimals(self):
        content = (
            "[PROPOSAL]\n"
            "Title: Small tool\n"
            "Cost: $99.99\n"
            "Description: Budget tool.\n"
            "[/PROPOSAL]"
        )
        p = extract_proposal_from_response(content, "Tech Agent")
        assert p is not None
        assert p.estimated_cost == 99.99

    def test_cost_without_dollar_sign(self):
        content = (
            "[PROPOSAL]\n"
            "Title: Free tier setup\n"
            "Cost: 0\n"
            "Description: Use free tiers.\n"
            "[/PROPOSAL]"
        )
        p = extract_proposal_from_response(content, "Tech Agent")
        assert p is not None
        assert p.estimated_cost == 0.0

    def test_multiline_description(self):
        content = (
            "[PROPOSAL]\n"
            "Title: MVP app\n"
            "Cost: $5000\n"
            "Description: Build a React Native app.\n"
            "Include push notifications.\n"
            "Support iOS and Android.\n"
            "[/PROPOSAL]"
        )
        p = extract_proposal_from_response(content, "Product Agent")
        assert p is not None
        assert "React Native" in p.description
        assert "push notifications" in p.description
        assert "iOS and Android" in p.description

    def test_case_insensitive_tags(self):
        content = (
            "[proposal]\n"
            "Title: Lowercase test\n"
            "Cost: $100\n"
            "Description: Tags in lowercase.\n"
            "[/proposal]"
        )
        p = extract_proposal_from_response(content, "Test Agent")
        assert p is not None
        assert p.title == "Lowercase test"

    def test_proposal_with_surrounding_text(self):
        content = (
            "After careful analysis of the market, I believe we should proceed.\n\n"
            "Here is my formal proposal:\n\n"
            "[PROPOSAL]\n"
            "Title: Market research tool\n"
            "Cost: $500\n"
            "Description: Subscribe to Crunchbase for competitor data.\n"
            "[/PROPOSAL]\n\n"
            "I'm happy to discuss further."
        )
        p = extract_proposal_from_response(content, "Market Agent")
        assert p is not None
        assert p.title == "Market research tool"

    def test_no_proposal_returns_none(self):
        content = "I think we should focus on the MVP first. No formal proposal yet."
        assert extract_proposal_from_response(content, "Agent") is None

    def test_malformed_proposal_returns_none(self):
        content = (
            "[PROPOSAL]\n"
            "Title: Missing cost\n"
            "Description: No cost line here.\n"
            "[/PROPOSAL]"
        )
        assert extract_proposal_from_response(content, "Agent") is None

    def test_empty_content_returns_none(self):
        assert extract_proposal_from_response("", "Agent") is None


# ---------------------------------------------------------------------------
# extract_vote_from_response
# ---------------------------------------------------------------------------


class TestExtractVote:
    def test_approve_vote(self):
        content = (
            "I support this.\n\n"
            "[VOTE]\n"
            "Proposal: abc123\n"
            "Vote: approve\n"
            "Reasoning: Aligns with our budget.\n"
            "[/VOTE]"
        )
        v = extract_vote_from_response(content, "Finance Agent")
        assert v is not None
        assert v.proposal_id == "abc123"
        assert v.vote == "approve"
        assert v.agent == "Finance Agent"
        assert "budget" in v.reasoning

    def test_reject_vote(self):
        content = (
            "[VOTE]\n"
            "Proposal: def456\n"
            "Vote: reject\n"
            "Reasoning: Too expensive.\n"
            "[/VOTE]"
        )
        v = extract_vote_from_response(content, "Finance Agent")
        assert v is not None
        assert v.vote == "reject"

    def test_abstain_vote(self):
        content = (
            "[VOTE]\n"
            "Proposal: ghi789\n"
            "Vote: abstain\n"
            "[/VOTE]"
        )
        v = extract_vote_from_response(content, "Risk Agent")
        assert v is not None
        assert v.vote == "abstain"
        assert v.reasoning == ""

    def test_vote_case_insensitive(self):
        content = (
            "[VOTE]\n"
            "Proposal: abc123\n"
            "Vote: APPROVE\n"
            "Reasoning: Looks good.\n"
            "[/VOTE]"
        )
        v = extract_vote_from_response(content, "Tech Agent")
        assert v is not None
        assert v.vote == "approve"

    def test_vote_without_reasoning(self):
        content = (
            "[VOTE]\n"
            "Proposal: abc123\n"
            "Vote: approve\n"
            "[/VOTE]"
        )
        v = extract_vote_from_response(content, "Market Agent")
        assert v is not None
        assert v.reasoning == ""

    def test_no_vote_returns_none(self):
        content = "I need more information before I can vote."
        assert extract_vote_from_response(content, "Agent") is None

    def test_empty_content_returns_none(self):
        assert extract_vote_from_response("", "Agent") is None

    def test_vote_with_surrounding_text(self):
        content = (
            "After reviewing the proposal, I have concerns about the timeline "
            "but the budget is acceptable.\n\n"
            "[VOTE]\n"
            "Proposal: xyz999\n"
            "Vote: approve\n"
            "Reasoning: Budget is within limits despite timeline concerns.\n"
            "[/VOTE]\n\n"
            "Let me know if you need more details."
        )
        v = extract_vote_from_response(content, "Finance Agent")
        assert v is not None
        assert v.proposal_id == "xyz999"
        assert v.vote == "approve"
