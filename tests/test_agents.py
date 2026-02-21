"""Tests for agent configs, base agent structure, and definitions."""

# conftest.py sets dummy API keys before this module loads.

import pytest

from agents.base import AgentConfig, AgentResponse, BaseAgent
from agents.definitions import AGENT_CONFIGS, get_agent


class TestAgentConfig:
    def test_all_five_agents_defined(self):
        expected = {"market", "product", "tech", "finance", "risk"}
        assert set(AGENT_CONFIGS.keys()) == expected

    def test_each_agent_has_required_fields(self):
        for name, cfg in AGENT_CONFIGS.items():
            assert cfg.name, f"{name} missing name"
            assert cfg.role, f"{name} missing role"
            assert cfg.domain, f"{name} missing domain"
            assert cfg.system_prompt, f"{name} missing system_prompt"
            assert cfg.model, f"{name} missing model"
            assert cfg.top_k > 0, f"{name} has invalid top_k"

    def test_agent_domains_are_unique(self):
        domains = [cfg.domain for cfg in AGENT_CONFIGS.values()]
        assert len(domains) == len(set(domains)), "Agent domains must be unique"

    def test_agent_names_are_unique(self):
        names = [cfg.name for cfg in AGENT_CONFIGS.values()]
        assert len(names) == len(set(names)), "Agent names must be unique"

    def test_system_prompts_are_substantial(self):
        for name, cfg in AGENT_CONFIGS.items():
            assert len(cfg.system_prompt) > 100, (
                f"{name} system prompt too short ({len(cfg.system_prompt)} chars)"
            )

    def test_config_defaults_applied(self):
        cfg = AgentConfig(
            name="Test",
            role="Test role",
            domain="test",
            system_prompt="Test prompt",
        )
        assert cfg.model != ""
        assert cfg.top_k > 0

    def test_config_custom_values_preserved(self):
        cfg = AgentConfig(
            name="Test",
            role="Test role",
            domain="test",
            system_prompt="Test prompt",
            model="claude-haiku-4-5-20251001",
            top_k=3,
        )
        assert cfg.model == "claude-haiku-4-5-20251001"
        assert cfg.top_k == 3


class TestAgentResponse:
    def test_response_creation(self):
        r = AgentResponse(agent="Test", role="Tester", content="Hello")
        assert r.agent == "Test"
        assert r.role == "Tester"
        assert r.content == "Hello"
        assert r.citations == []
        assert r.sources_used == 0

    def test_response_with_citations(self):
        r = AgentResponse(
            agent="Market Agent",
            role="Research",
            content="The market is $300B",
            citations=[{"cited_text": "300B", "source": "report.pdf"}],
            sources_used=3,
        )
        assert len(r.citations) == 1
        assert r.sources_used == 3


class TestGetAgent:
    def test_get_valid_agent(self):
        for name in AGENT_CONFIGS:
            agent = get_agent(name)
            assert isinstance(agent, BaseAgent)
            assert agent.config.domain == name

    def test_get_invalid_agent_raises(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            get_agent("nonexistent")

    def test_get_agent_with_shared_retriever(self):
        """Agents should accept a shared retriever instance."""
        # We can't create a real Retriever without API keys, but we can test
        # that get_agent accepts the parameter
        agent1 = get_agent("market")
        agent2 = get_agent("tech", retriever=agent1.retriever)
        assert agent2.retriever is agent1.retriever


class TestAgentPersonalities:
    """Verify agent prompts contain expected personality traits."""

    def test_market_agent_is_data_focused(self):
        prompt = AGENT_CONFIGS["market"].system_prompt.lower()
        assert "data" in prompt
        assert "market" in prompt
        assert "research" in prompt

    def test_product_agent_is_user_focused(self):
        prompt = AGENT_CONFIGS["product"].system_prompt.lower()
        assert "user" in prompt or "mvp" in prompt
        assert "feature" in prompt

    def test_tech_agent_is_pragmatic(self):
        prompt = AGENT_CONFIGS["tech"].system_prompt.lower()
        assert "pragmatic" in prompt or "conservative" in prompt
        assert "cost" in prompt or "complexity" in prompt

    def test_finance_agent_is_cost_focused(self):
        prompt = AGENT_CONFIGS["finance"].system_prompt.lower()
        assert "budget" in prompt
        assert "runway" in prompt
        assert "cost" in prompt

    def test_risk_agent_is_compliance_focused(self):
        prompt = AGENT_CONFIGS["risk"].system_prompt.lower()
        assert "risk" in prompt
        assert "legal" in prompt or "compliance" in prompt

    def test_agents_have_conflicting_priorities(self):
        """Product vs Tech, Product vs Finance — the spec says they argue."""
        product_prompt = AGENT_CONFIGS["product"].system_prompt.lower()
        tech_prompt = AGENT_CONFIGS["tech"].system_prompt.lower()
        finance_prompt = AGENT_CONFIGS["finance"].system_prompt.lower()

        # Product wants features, Tech warns about complexity
        assert "feature" in product_prompt
        assert "complexity" in tech_prompt or "simplicity" in tech_prompt

        # Finance blocks spending
        assert "block" in finance_prompt
