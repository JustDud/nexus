"""Simple event bus for simulation lifecycle events."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


# Event type constants
SIMULATION_STARTED = "simulation_started"
PHASE_CHANGED = "phase_changed"
AGENT_THINKING = "agent_thinking"
AGENT_SPEAKING = "agent_speaking"
PROPOSAL_CREATED = "proposal_created"
VOTE_CAST = "vote_cast"
BUDGET_UPDATED = "budget_updated"
CONSENSUS_REACHED = "consensus_reached"
DEBATE_ROUND_COMPLETE = "debate_round_complete"
PROPOSAL_ESCALATED = "proposal_escalated"
PROPOSAL_EXECUTED = "proposal_executed"
SIMULATION_COMPLETED = "simulation_completed"

# Callback type: async function taking (event_type, data)
Listener = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


@dataclass
class EventBus:
    """Async pub/sub event bus for simulation events."""

    _listeners: dict[str, list[Listener]] = field(default_factory=dict)

    def on(self, event_type: str, callback: Listener) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(callback)

    def off(self, event_type: str, callback: Listener) -> None:
        """Remove a listener."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb is not callback
            ]

    async def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Emit an event to all registered listeners."""
        data = data or {}
        for callback in self._listeners.get(event_type, []):
            await callback(event_type, data)

    async def emit_concurrent(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Emit an event, running all listeners concurrently."""
        data = data or {}
        tasks = [callback(event_type, data) for callback in self._listeners.get(event_type, [])]
        if tasks:
            await asyncio.gather(*tasks)
