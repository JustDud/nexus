"""
Event bus for simulation pub-sub.

Supports both Queue-based subscribers (for SSE streaming) and the simple
emit(event_type_str, data) call pattern used by the orchestrator and debate manager.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """All event types in a simulation."""

    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    PHASE_CHANGED = "phase_changed"
    ROUND_STARTED = "round_started"
    ROUND_COMPLETED = "round_completed"
    AGENT_THINKING = "agent_thinking"
    AGENT_SPEAKING = "agent_speaking"
    AGENT_RESPONSE = "agent_response"
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_ESCALATED = "proposal_escalated"
    PROPOSAL_EXECUTED = "proposal_executed"
    VOTE_CAST = "vote_cast"
    DEBATE_STARTED = "debate_started"
    DEBATE_RESPONSE = "debate_response"
    DEBATE_ROUND_COMPLETE = "debate_round_complete"
    CONSENSUS_REACHED = "consensus_reached"
    DECISION_NEEDED = "decision_needed"
    DECISION_MADE = "decision_made"
    BUDGET_UPDATED = "budget_updated"
    ERROR = "error"


# String constants — used by debate.py and orchestrator.py imports
SIMULATION_STARTED = EventType.SIMULATION_STARTED.value
SIMULATION_COMPLETED = EventType.SIMULATION_COMPLETED.value
PHASE_CHANGED = EventType.PHASE_CHANGED.value
AGENT_THINKING = EventType.AGENT_THINKING.value
AGENT_SPEAKING = EventType.AGENT_SPEAKING.value
PROPOSAL_CREATED = EventType.PROPOSAL_CREATED.value
PROPOSAL_ESCALATED = EventType.PROPOSAL_ESCALATED.value
PROPOSAL_EXECUTED = EventType.PROPOSAL_EXECUTED.value
VOTE_CAST = EventType.VOTE_CAST.value
CONSENSUS_REACHED = EventType.CONSENSUS_REACHED.value
DEBATE_ROUND_COMPLETE = EventType.DEBATE_ROUND_COMPLETE.value
BUDGET_UPDATED = EventType.BUDGET_UPDATED.value


@dataclass
class SimulationEvent:
    event_type: EventType | str
    data: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if isinstance(self.event_type, str):
            try:
                self.event_type = EventType(self.event_type)
            except ValueError:
                pass

    def to_sse(self) -> str:
        """Format as Server-Sent Event line pair."""
        et = self.event_type.value if isinstance(self.event_type, EventType) else self.event_type
        payload = json.dumps({"event_type": et, "data": self.data, "timestamp": self.timestamp})
        return f"event: {et}\ndata: {payload}\n\n"


class EventBus:
    """Async event bus with Queue-based subscribers and event history.

    Supports two call styles:
        await bus.emit(SimulationEvent(...))         # routes / SSE
        await bus.emit("agent_thinking", {...})      # orchestrator / debate
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, asyncio.Queue[SimulationEvent]] = {}
        self._history: list[SimulationEvent] = []

    async def emit(self, event_or_type: SimulationEvent | str, data: dict[str, Any] | None = None) -> None:
        """Emit an event to all subscriber queues, callbacks, and record in history."""
        if isinstance(event_or_type, SimulationEvent):
            event = event_or_type
        else:
            event = SimulationEvent(event_type=event_or_type, data=data or {})

        self._history.append(event)
        for queue in list(self._subscribers.values()):
            await queue.put(event)

        # Also notify callback listeners (used by debate tests)
        et = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type
        if hasattr(self, "_listeners"):
            for callback in self._listeners.get(et, []):
                await callback(et, event.data)

    def subscribe(self) -> tuple[str, asyncio.Queue[SimulationEvent]]:
        """Create a new subscriber. Returns (subscriber_id, queue)."""
        sub_id = uuid.uuid4().hex[:8]
        queue: asyncio.Queue[SimulationEvent] = asyncio.Queue()
        self._subscribers[sub_id] = queue
        return sub_id, queue

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber by ID."""
        self._subscribers.pop(subscriber_id, None)

    # Callback-based listener support (used by tests)
    def on(self, event_type: str, callback: Any) -> None:
        """Register a callback listener (legacy interface for tests)."""
        if not hasattr(self, "_listeners"):
            self._listeners: dict[str, list] = {}
        self._listeners.setdefault(event_type, []).append(callback)

    @property
    def history(self) -> list[SimulationEvent]:
        """All events emitted so far, in order."""
        return list(self._history)
