"""Simulation state management — phases, budget, messages, and the central state object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Phase(StrEnum):
    SETUP = "SETUP"
    RESEARCH = "RESEARCH"
    PROPOSAL = "PROPOSAL"
    DEBATE = "DEBATE"
    DECISION = "DECISION"
    EXECUTION = "EXECUTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Transaction:
    id: str
    description: str
    amount: float  # negative = spend
    approved_by: str
    timestamp: datetime
    category: str


@dataclass
class AgentMessage:
    agent: str
    role: str
    content: str
    phase: Phase
    round_number: int = 0
    citations: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BudgetTracker:
    initial_budget: float
    transactions: list[Transaction] = field(default_factory=list)

    @property
    def total_spent(self) -> float:
        return abs(sum(t.amount for t in self.transactions if t.amount < 0))

    @property
    def remaining(self) -> float:
        return self.initial_budget - self.total_spent

    @property
    def burn_rate_per_transaction(self) -> float:
        spending = [t for t in self.transactions if t.amount < 0]
        if not spending:
            return 0.0
        return self.total_spent / len(spending)

    def can_afford(self, amount: float) -> bool:
        return self.remaining >= amount

    def record(
        self,
        description: str,
        amount: float,
        approved_by: str,
        category: str,
    ) -> Transaction:
        txn = Transaction(
            id=str(uuid.uuid4()),
            description=description,
            amount=amount,
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc),
            category=category,
        )
        self.transactions.append(txn)
        return txn


@dataclass
class SimulationState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    startup_idea: str = ""
    initial_budget: float = 0.0
    budget: BudgetTracker = field(default_factory=lambda: BudgetTracker(initial_budget=0.0))
    phase: Phase = Phase.SETUP
    conversation: list[AgentMessage] = field(default_factory=list)
    current_round: int = 0
    max_debate_rounds: int = 2
    pending_proposals: list[Any] = field(default_factory=list)
    decided_proposals: list[Any] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_phases: list[str] = field(default_factory=list)

    def initialize(self, idea: str, budget: float) -> None:
        self.startup_idea = idea
        self.initial_budget = budget
        self.budget = BudgetTracker(initial_budget=budget)
        self.phase = Phase.RESEARCH

    def add_message(
        self,
        agent: str,
        role: str,
        content: str,
        phase: Phase,
        round_number: int = 0,
        citations: list[dict] | None = None,
    ) -> AgentMessage:
        msg = AgentMessage(
            agent=agent,
            role=role,
            content=content,
            phase=phase,
            round_number=round_number,
            citations=citations or [],
        )
        self.conversation.append(msg)
        return msg

    def format_full_conversation(self) -> str:
        """Format the entire conversation history across all phases.

        Every agent sees what every other agent has said so far,
        regardless of which phase the messages originated from.
        """
        if not self.conversation:
            return "(No prior conversation.)"
        lines: list[str] = []
        current_phase = None
        for m in self.conversation:
            if m.phase != current_phase:
                current_phase = m.phase
                lines.append(f"\n--- {current_phase} ---")
            header = f"{m.agent} ({m.role})"
            if m.round_number:
                header += f" [Round {m.round_number}]"
            lines.append(f"{header}:\n{m.content}\n")
        return "\n".join(lines)

    def get_context_dict(self) -> dict:
        """Return the context dict that BaseAgent.query(context=...) expects."""
        return {
            "startup_idea": self.startup_idea,
            "budget_remaining": self.budget.remaining,
            "budget_initial": self.initial_budget,
            "total_spent": self.budget.total_spent,
            "phase": str(self.phase),
            "round": self.current_round,
            "conversation": self.format_full_conversation(),
        }
