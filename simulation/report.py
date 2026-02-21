"""
Report generation from simulation event history.

Reconstructs what happened in a session by replaying its EventBus history.
When Dima's SimulationState is integrated, this will also pull budget
snapshots and round details from state directly.
"""

from dataclasses import dataclass, field

from simulation.events import EventType
from simulation.session import Session


@dataclass
class SimulationReport:
    session_id: str
    idea: str
    initial_budget: float
    final_budget: float
    status: str
    rounds_completed: int
    proposals: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    key_events: list[dict] = field(default_factory=list)
    summary: str = ""


def generate_report(session: Session) -> SimulationReport:
    """Build a summary report from a session's event history and state."""
    events = session.event_bus.history

    proposals = []
    decisions = []
    key_events = []
    rounds_completed = 0

    for event in events:
        if event.event_type == EventType.PROPOSAL_CREATED:
            proposals.append(event.data)
        elif event.event_type == EventType.DECISION_MADE:
            decisions.append(event.data)
        elif event.event_type == EventType.ROUND_COMPLETED:
            rounds_completed += 1
        elif event.event_type in (
            EventType.SIMULATION_STARTED,
            EventType.SIMULATION_COMPLETED,
            EventType.ERROR,
        ):
            key_events.append(
                {
                    "type": event.event_type.value,
                    "data": event.data,
                    "timestamp": event.timestamp,
                }
            )

    # Determine final budget: from state if available, else from session
    final_budget = session.budget
    if session.state is not None and hasattr(session.state, "budget"):
        final_budget = session.state.budget

    approved = sum(1 for d in decisions if d.get("approved"))
    rejected = len(decisions) - approved
    summary = (
        f'Simulation for "{session.idea}" completed {rounds_completed} rounds. '
        f"{len(proposals)} proposals were made, {approved} approved, {rejected} rejected. "
        f"Budget: ${session.budget:,.2f} -> ${final_budget:,.2f}."
    )

    return SimulationReport(
        session_id=session.session_id,
        idea=session.idea,
        initial_budget=session.budget,
        final_budget=final_budget,
        status=session.status,
        rounds_completed=rounds_completed,
        proposals=proposals,
        decisions=decisions,
        key_events=key_events,
        summary=summary,
    )
