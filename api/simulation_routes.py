"""
Simulation API endpoints.

6 endpoints for managing simulation sessions, streaming events via SSE,
making CEO decisions, and generating reports.
"""

import asyncio
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from simulation.events import EventType, SimulationEvent
from simulation.report import generate_report
from simulation.session import create_session, get_session, list_sessions

sim_router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class StartSimulationRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Startup idea to simulate")
    budget: float = Field(..., gt=0, description="Starting budget in dollars")


class DecisionRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    approved: bool
    note: str = ""


# ---------------------------------------------------------------------------
# Background runner
# ---------------------------------------------------------------------------


async def _run_simulation(session):
    """Run the orchestrator in the background, updating session status."""
    try:
        await session.orchestrator.start(session.idea, session.budget)
        await session.orchestrator.run_until_decision()

        if session.state.phase.value == "DECISION":
            session.status = "paused"
        elif session.state.phase.value in ("COMPLETED", "FAILED"):
            session.status = session.state.phase.value.lower()
    except Exception as e:
        session.status = "failed"
        await session.event_bus.emit(
            SimulationEvent(event_type=EventType.ERROR, data={"error": str(e)})
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@sim_router.post("/simulation/start")
async def start_simulation(req: StartSimulationRequest):
    """Start a new simulation session."""
    session = create_session(idea=req.idea, budget=req.budget)
    session.status = "running"

    # Record the start event immediately (before background task)
    await session.event_bus.emit(
        SimulationEvent(
            event_type=EventType.SIMULATION_STARTED,
            data={"idea": req.idea, "budget": req.budget},
        )
    )

    # Launch the orchestrator as a background task
    asyncio.create_task(_run_simulation(session))

    return {
        "session_id": session.session_id,
        "idea": session.idea,
        "budget": session.budget,
        "status": session.status,
        "created_at": session.created_at,
    }


@sim_router.get("/simulation/sessions")
async def list_all_sessions():
    """List all simulation sessions, most recent first."""
    sessions = list_sessions()
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "idea": s.idea,
                "budget": s.budget,
                "status": s.status,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
    }


@sim_router.get("/simulation/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """Get detailed info for a specific session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {
        "session_id": session.session_id,
        "idea": session.idea,
        "budget": session.budget,
        "status": session.status,
        "created_at": session.created_at,
        "phase": str(session.state.phase),
        "budget_remaining": session.state.budget.remaining,
        "total_spent": session.state.budget.total_spent,
        "event_count": len(session.event_bus.history),
        "pending_proposals": [p.to_decision_card() for p in session.state.pending_proposals],
        "conversation_length": len(session.state.conversation),
    }


@sim_router.get("/simulation/sessions/{session_id}/events")
async def stream_events(session_id: str):
    """Stream simulation events via SSE."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    sub_id, queue = session.event_bus.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse()
                    if event.event_type == EventType.SIMULATION_COMPLETED:
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            session.event_bus.unsubscribe(sub_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@sim_router.post("/simulation/sessions/{session_id}/decide")
async def make_decision(session_id: str, req: DecisionRequest):
    """CEO approves or rejects a proposal. Resumes simulation if all decisions resolved."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    if session.status != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Session is '{session.status}', must be 'paused' to make decisions",
        )

    await session.orchestrator.resolve_ceo_decision(
        proposal_id=req.proposal_id,
        approved=req.approved,
        note=req.note,
    )

    # If no more pending proposals, resume simulation
    if not session.state.pending_proposals:
        session.status = "running"
        asyncio.create_task(_run_simulation_resume(session))

    return {
        "session_id": session_id,
        "proposal_id": req.proposal_id,
        "approved": req.approved,
        "status": session.status,
        "budget_remaining": session.state.budget.remaining,
    }


async def _run_simulation_resume(session):
    """Resume orchestrator after CEO decisions, updating session status."""
    try:
        await session.orchestrator.run_until_decision()

        if session.state.phase.value == "DECISION":
            session.status = "paused"
        elif session.state.phase.value in ("COMPLETED", "FAILED"):
            session.status = session.state.phase.value.lower()
    except Exception as e:
        session.status = "failed"
        await session.event_bus.emit(
            SimulationEvent(event_type=EventType.ERROR, data={"error": str(e)})
        )


@sim_router.get("/simulation/sessions/{session_id}/report")
async def get_report(session_id: str):
    """Generate a summary report for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    report = generate_report(session)
    return asdict(report)
