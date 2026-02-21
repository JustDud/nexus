"""Simulation state tracking: phases, budget, and transactions."""

from dataclasses import dataclass, field
from enum import Enum


class Phase(str, Enum):
    """Simulation phases matching frontend SimulationStage type."""
    RESEARCHING = "researching"
    PLANNING = "planning"
    BUILDING = "building"
    DEPLOYING = "deploying"
    OPERATING = "operating"
    COMPLETE = "complete"


@dataclass
class Transaction:
    agent_id: str       # frontend agent ID: "product", "tech", "ops", "finance"
    description: str
    amount: float
    approved: bool


@dataclass
class BudgetTracker:
    total: float
    spent: float = 0.0
    transactions: list[Transaction] = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return self.total - self.spent

    def can_spend(self, amount: float) -> bool:
        return amount <= self.remaining

    def record(self, tx: Transaction) -> None:
        self.transactions.append(tx)
        if tx.approved:
            self.spent += tx.amount


@dataclass
class SimulationState:
    idea: str
    phase: Phase = Phase.RESEARCHING
    budget: BudgetTracker = field(default_factory=lambda: BudgetTracker(total=0))
    agent_outputs: dict[str, str] = field(default_factory=dict)
    operations_round: int = 0
    round_label: str = ""
