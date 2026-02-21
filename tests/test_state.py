"""Tests for simulation/state.py — Phase, BudgetTracker, SimulationState."""

import pytest

from simulation.state import BudgetTracker, Phase, SimulationState, Transaction


class TestPhaseEnum:
    def test_phase_values(self):
        assert Phase.RESEARCHING.value == "researching"
        assert Phase.PLANNING.value == "planning"
        assert Phase.BUILDING.value == "building"
        assert Phase.DEPLOYING.value == "deploying"
        assert Phase.COMPLETE.value == "complete"

    def test_phase_is_string(self):
        assert isinstance(Phase.RESEARCHING, str)
        assert Phase.BUILDING == "building"


class TestTransaction:
    def test_transaction_fields(self):
        tx = Transaction(
            agent_id="tech", description="Cloud hosting", amount=500.0, approved=True
        )
        assert tx.agent_id == "tech"
        assert tx.description == "Cloud hosting"
        assert tx.amount == 500.0
        assert tx.approved is True


class TestBudgetTracker:
    def test_initial_state(self):
        bt = BudgetTracker(total=10000)
        assert bt.total == 10000
        assert bt.spent == 0.0
        assert bt.remaining == 10000
        assert bt.transactions == []

    def test_can_spend_within_budget(self):
        bt = BudgetTracker(total=1000)
        assert bt.can_spend(500) is True
        assert bt.can_spend(1000) is True

    def test_can_spend_over_budget(self):
        bt = BudgetTracker(total=1000)
        assert bt.can_spend(1001) is False

    def test_can_spend_after_spending(self):
        bt = BudgetTracker(total=1000)
        tx = Transaction(agent_id="tech", description="X", amount=600, approved=True)
        bt.record(tx)
        assert bt.can_spend(400) is True
        assert bt.can_spend(401) is False

    def test_record_approved_updates_spent(self):
        bt = BudgetTracker(total=5000)
        tx = Transaction(agent_id="tech", description="AWS", amount=1200, approved=True)
        bt.record(tx)
        assert bt.spent == 1200
        assert bt.remaining == 3800
        assert len(bt.transactions) == 1

    def test_record_blocked_does_not_update_spent(self):
        bt = BudgetTracker(total=5000)
        tx = Transaction(
            agent_id="tech", description="Too expensive", amount=9000, approved=False
        )
        bt.record(tx)
        assert bt.spent == 0.0
        assert bt.remaining == 5000
        assert len(bt.transactions) == 1

    def test_multiple_transactions(self):
        bt = BudgetTracker(total=3000)
        bt.record(Transaction("tech", "Hosting", 500, True))
        bt.record(Transaction("product", "Design tool", 200, True))
        bt.record(Transaction("ops", "Legal review", 5000, False))
        assert bt.spent == 700
        assert bt.remaining == 2300
        assert len(bt.transactions) == 3

    def test_can_spend_zero(self):
        bt = BudgetTracker(total=100)
        assert bt.can_spend(0) is True

    def test_remaining_property(self):
        bt = BudgetTracker(total=2000, spent=750)
        assert bt.remaining == 1250


class TestSimulationState:
    def test_defaults(self):
        state = SimulationState(idea="Test idea")
        assert state.idea == "Test idea"
        assert state.phase == Phase.RESEARCHING
        assert state.budget.total == 0
        assert state.agent_outputs == {}

    def test_custom_budget(self):
        state = SimulationState(
            idea="AI app", budget=BudgetTracker(total=5000)
        )
        assert state.budget.total == 5000
        assert state.budget.remaining == 5000

    def test_phase_progression(self):
        state = SimulationState(idea="Test")
        state.phase = Phase.PLANNING
        assert state.phase == Phase.PLANNING
        state.phase = Phase.COMPLETE
        assert state.phase == Phase.COMPLETE

    def test_agent_outputs_dict(self):
        state = SimulationState(idea="Test")
        state.agent_outputs["market_researching"] = "Market is big"
        state.agent_outputs["tech_planning"] = "Use React"
        assert len(state.agent_outputs) == 2
        assert "Market is big" in state.agent_outputs["market_researching"]
