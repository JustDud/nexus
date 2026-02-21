"""
In-memory simulation session management.

Each session holds an EventBus, SimulationState, and SimulationOrchestrator
wired together. The orchestrator drives the simulation; the session is the
handle the API layer uses to interact with it.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from simulation.events import EventBus
from simulation.orchestrator import SimulationOrchestrator
from simulation.state import SimulationState

# In-memory session store
_sessions: dict[str, "Session"] = {}


@dataclass
class Session:
    session_id: str
    idea: str
    budget: float
    status: str = "pending"  # "pending" | "running" | "paused" | "completed" | "failed"
    event_bus: EventBus = field(default_factory=EventBus)
    created_at: str = ""
    state: SimulationState = field(default_factory=SimulationState)
    orchestrator: SimulationOrchestrator | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.orchestrator = SimulationOrchestrator(state=self.state, event_bus=self.event_bus)


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
