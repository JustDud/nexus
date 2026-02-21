"""
Event bus for simulation pub-sub.

One EventBus per session. Subscribers (SSE clients) each get their own
asyncio.Queue. When emit() is called, the event is pushed to every active
subscriber queue.
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class EventType(str, Enum):
    """All event types in a simulation. str mixin for JSON serialization."""

    SIMULATION_STARTED = "simulation_started"
    ROUND_STARTED = "round_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    PROPOSAL_CREATED = "proposal_created"
    VOTE_CAST = "vote_cast"
    DEBATE_STARTED = "debate_started"
    DEBATE_RESPONSE = "debate_response"
    DECISION_NEEDED = "decision_needed"
    DECISION_MADE = "decision_made"
    BUDGET_UPDATED = "budget_updated"
    ROUND_COMPLETED = "round_completed"
    SIMULATION_COMPLETED = "simulation_completed"
    ERROR = "error"


@dataclass
class SimulationEvent:
    event_type: EventType
    data: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_sse(self) -> str:
        """Format as Server-Sent Event line pair."""
        payload = json.dumps(asdict(self))
        return f"event: {self.event_type.value}\ndata: {payload}\n\n"


class EventBus:
    """Async pub-sub event bus. One per simulation session."""

    def __init__(self):
        self._subscribers: dict[str, asyncio.Queue[SimulationEvent]] = {}
        self._history: list[SimulationEvent] = []

    async def emit(self, event: SimulationEvent) -> None:
        """Push event to all subscriber queues and append to history."""
        self._history.append(event)
        # Snapshot to avoid RuntimeError if a subscriber disconnects mid-emit
        queues = list(self._subscribers.values())
        for queue in queues:
            await queue.put(event)

    def subscribe(self) -> tuple[str, asyncio.Queue[SimulationEvent]]:
        """Create a new subscriber. Returns (subscriber_id, queue)."""
        sub_id = uuid.uuid4().hex[:8]
        queue: asyncio.Queue[SimulationEvent] = asyncio.Queue()
        self._subscribers[sub_id] = queue
        return sub_id, queue

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber by ID. Silent if not found."""
        self._subscribers.pop(subscriber_id, None)

    @property
    def history(self) -> list[SimulationEvent]:
        """All events emitted so far, in order."""
        return list(self._history)
