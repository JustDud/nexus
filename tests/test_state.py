"""Tests for simulation state management."""

from simulation.state import BudgetTracker, Phase, SimulationState


class TestBudgetTracker:
    def test_empty_state(self):
        bt = BudgetTracker(initial_budget=10_000)
        assert bt.total_spent == 0.0
        assert bt.remaining == 10_000
        assert bt.burn_rate_per_transaction == 0.0
        assert bt.transactions == []

    def test_record_transaction(self):
        bt = BudgetTracker(initial_budget=10_000)
        txn = bt.record("Cloud hosting", -500, approved_by="Finance Agent", category="infrastructure")
        assert txn.amount == -500
        assert txn.description == "Cloud hosting"
        assert txn.category == "infrastructure"
        assert txn.approved_by == "Finance Agent"
        assert txn.id  # uuid is set
        assert len(bt.transactions) == 1

    def test_remaining_after_spend(self):
        bt = BudgetTracker(initial_budget=10_000)
        bt.record("Hosting", -2_000, approved_by="Finance", category="infrastructure")
        bt.record("Marketing", -3_000, approved_by="Finance", category="marketing")
        assert bt.total_spent == 5_000
        assert bt.remaining == 5_000

    def test_can_afford(self):
        bt = BudgetTracker(initial_budget=1_000)
        assert bt.can_afford(1_000) is True
        assert bt.can_afford(1_001) is False
        bt.record("Spend", -600, approved_by="Finance", category="ops")
        assert bt.can_afford(400) is True
        assert bt.can_afford(401) is False

    def test_burn_rate(self):
        bt = BudgetTracker(initial_budget=10_000)
        bt.record("A", -1_000, approved_by="F", category="eng")
        bt.record("B", -3_000, approved_by="F", category="eng")
        assert bt.burn_rate_per_transaction == 2_000  # 4000 total / 2 txns


class TestSimulationState:
    def test_initialize(self):
        state = SimulationState()
        state.initialize("AI dog walker", 50_000)
        assert state.startup_idea == "AI dog walker"
        assert state.initial_budget == 50_000
        assert state.budget.initial_budget == 50_000
        assert state.phase == Phase.RESEARCH

    def test_get_context_dict(self):
        state = SimulationState()
        state.initialize("AI dog walker", 50_000)
        ctx = state.get_context_dict()
        assert ctx["startup_idea"] == "AI dog walker"
        assert ctx["budget_remaining"] == 50_000
        assert ctx["budget_initial"] == 50_000
        assert ctx["total_spent"] == 0.0
        assert ctx["phase"] == "RESEARCH"
        assert ctx["round"] == 0

    def test_get_context_dict_after_spending(self):
        state = SimulationState()
        state.initialize("AI dog walker", 50_000)
        state.budget.record("Hosting", -5_000, approved_by="Finance", category="infra")
        ctx = state.get_context_dict()
        assert ctx["budget_remaining"] == 45_000
        assert ctx["total_spent"] == 5_000

    def test_add_message(self):
        state = SimulationState()
        state.initialize("Test idea", 10_000)
        msg = state.add_message(
            agent="Market Agent",
            role="market_analyst",
            content="Market looks promising.",
            phase=Phase.RESEARCH,
            round_number=1,
            citations=[{"cited_text": "data point", "source": "report.pdf"}],
        )
        assert msg.agent == "Market Agent"
        assert msg.role == "market_analyst"
        assert msg.content == "Market looks promising."
        assert msg.phase == Phase.RESEARCH
        assert msg.round_number == 1
        assert len(msg.citations) == 1
        assert len(state.conversation) == 1

    def test_add_message_defaults(self):
        state = SimulationState()
        msg = state.add_message(
            agent="Tech Agent",
            role="engineer",
            content="Feasible.",
            phase=Phase.PROPOSAL,
        )
        assert msg.round_number == 0
        assert msg.citations == []

    def test_phase_transitions(self):
        state = SimulationState()
        assert state.phase == Phase.SETUP
        state.initialize("Idea", 10_000)
        assert state.phase == Phase.RESEARCH
        state.phase = Phase.PROPOSAL
        state.completed_phases.append("RESEARCH")
        assert state.phase == Phase.PROPOSAL
        assert "RESEARCH" in state.completed_phases

    def test_default_id_and_created_at(self):
        state = SimulationState()
        assert state.id  # uuid is set
        assert state.created_at is not None

    def test_max_debate_rounds_default(self):
        state = SimulationState()
        assert state.max_debate_rounds == 2
