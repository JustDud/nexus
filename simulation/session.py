"""
In-memory simulation session management.

Each session represents one simulation run and holds the idea, budget,
status, event bus, and a reference to the simulation state.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from simulation.events import EventBus
from simulation.proposals import Proposal

# In-memory session store (same pattern as _retriever in api/routes.py)
_sessions: dict[str, "Session"] = {}


@dataclass
class PendingDecision:
    proposal: Proposal
    agent_name: str
    phase: str
    decision_future: asyncio.Future


@dataclass
class Session:
    session_id: str
    idea: str
    budget: float
    status: str = "pending"  # "pending" | "running" | "paused" | "completed" | "failed" | "stopping"
    event_bus: EventBus = field(default_factory=EventBus)
    created_at: str = ""
    # Placeholder for Dima's SimulationState — duck-typed with hasattr checks
    state: object = None
    auto_approve_threshold: float = 25.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self._pending_decision: PendingDecision | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def request_decision(self, proposal: Proposal, agent_name: str, phase: str) -> dict:
        """Create a Future, store it as a PendingDecision, pause, and await."""
        loop = asyncio.get_running_loop()
        self._loop = loop
        future = loop.create_future()
        self._pending_decision = PendingDecision(
            proposal=proposal,
            agent_name=agent_name,
            phase=phase,
            decision_future=future,
        )
        self.status = "paused"
        result = await future
        return result

    def resolve_decision(self, approved: bool, reason: str = "") -> None:
        """Resolve the pending decision future (thread-safe)."""
        if self._pending_decision is None:
            return
        future = self._pending_decision.decision_future
        loop = self._loop
        if loop is not None and not future.done():
            loop.call_soon_threadsafe(future.set_result, {"approved": approved, "reason": reason})
        self._pending_decision = None
        self.status = "running"


def create_session(idea: str, budget: float) -> Session:
    """Create a new simulation session and store it."""
    session_id = uuid.uuid4().hex[:12]
    session = Session(session_id=session_id, idea=idea, budget=budget)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Session | None:
    """Retrieve a session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def list_sessions() -> list[Session]:
    """Return all sessions, most recent first."""
    return sorted(_sessions.values(), key=lambda s: s.created_at, reverse=True)


def get_event_bus(session_id: str) -> EventBus | None:
    """Convenience: get the EventBus for a session."""
    session = _sessions.get(session_id)
    return session.event_bus if session else None
