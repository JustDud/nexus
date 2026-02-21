"""WebSocket endpoint for real-time simulation streaming."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from simulation.events import EventType, SimulationEvent
from simulation.orchestrator import run_simulation
from simulation.session import create_session
from simulation.voice import should_voice_event, synthesize_for_agent

logger = logging.getLogger(__name__)

ws_router = APIRouter()


def translate_event(event: SimulationEvent) -> list[dict] | None:
    """Convert a backend SimulationEvent to frontend WS message(s).

    Returns a list of messages to send, or None to skip.
    """
    et = event.event_type
    d = event.data

    if et == EventType.AGENT_THINKING:
        return [{
            "type": "agent_thinking",
            "agentId": d.get("agent_id", "tech"),
            "fragments": [f"{d.get('agent_name', 'Agent')} is analyzing..."],
        }]

    if et == EventType.AGENT_RESPONSE:
        agent_id = d.get("agent_id", "tech")
        content = d.get("content", "")
        sentences = [s.strip() for s in content.split(".") if s.strip()][:4]
        summary = content[:120] + "..." if len(content) > 120 else content
        return [
            {
                "type": "agent_thinking",
                "agentId": agent_id,
                "fragments": sentences if sentences else ["Processing..."],
            },
            {
                "type": "agent_acting",
                "agentId": agent_id,
                "action": summary,
            },
        ]

    if et == EventType.AGENT_SPEAKING:
        agent_id = d.get("agent_id", "tech")
        content = d.get("content", "")
        sentences = [s.strip() for s in content.split(".") if s.strip()][:3]
        summary = content[:120] + "..." if len(content) > 120 else content
        return [
            {
                "type": "agent_thinking",
                "agentId": agent_id,
                "fragments": sentences if sentences else ["Debating..."],
            },
            {
                "type": "agent_acting",
                "agentId": agent_id,
                "action": summary,
            },
        ]

    if et == EventType.VOTE_CAST:
        return [{
            "type": "agent_acting",
            "agentId": d.get("agent_id", "tech"),
            "action": f"Voted: {d.get('stance', 'unknown').upper()}",
        }]

    if et == EventType.BUDGET_UPDATED:
        msgs = []
        # Only send transaction if there's a specific expense described
        if d.get("description"):
            msgs.append({
                "type": "transaction",
                "agentId": d.get("agent_id", "finance"),
                "description": d.get("description", "Expense"),
                "amount": d.get("amount", 0),
                "status": "approved" if d.get("approved") else "blocked",
            })
        msgs.append({
            "type": "budget_update",
            "spent": d.get("total_spent", d.get("spent", 0)),
            "total": d.get("initial", d.get("total", 0)),
            "remaining": d.get("remaining", 0),
        })
        return msgs

    if et == EventType.PHASE_CHANGED:
        # Map orchestrator phases to frontend stages
        phase = d.get("phase", "").upper()
        phase_to_stage = {
            "RESEARCH": "researching",
            "PROPOSAL": "planning",
            "DEBATE": "planning",
            "DECISION": "planning",
            "EXECUTION": "building",
            "COMPLETED": "complete",
            "FAILED": "complete",
        }
        stage = phase_to_stage.get(phase)
        if stage:
            return [{"type": "stage_change", "stage": stage}]
        return None

    if et == EventType.PROPOSAL_CREATED:
        return [{
            "type": "proposal_created",
            "proposalId": d.get("proposal_id", ""),
            "title": d.get("title", ""),
            "cost": d.get("cost", 0),
            "description": d.get("description", ""),
            "agentId": d.get("agent_id", ""),
        }]

    if et == EventType.DECISION_NEEDED:
        return [{
            "type": "approval_required",
            "proposalId": d.get("proposal_id", ""),
            "title": d.get("title", ""),
            "cost": d.get("cost", 0),
            "description": d.get("description", ""),
            "agentId": d.get("agent_id", ""),
            "agentName": d.get("agent_name", ""),
        }]

    if et == EventType.DECISION_MADE:
        return [{
            "type": "approval_resolved",
            "proposalId": d.get("proposal_id", ""),
            "approved": d.get("approved", False),
            "reason": d.get("reason", ""),
        }]

    if et == EventType.ROUND_STARTED:
        current_round = d.get("round", "")
        if current_round == "operating":
            return [{
                "type": "ops_round",
                "round": d.get("ops_round", 0),
                "label": d.get("label", ""),
            }]
        return None

    if et == EventType.ROUND_COMPLETED:
        current_round = d.get("round", "")
        if current_round == "operating":
            # Don't trigger stage_change for operating rounds
            return None
        stage_map = {
            "researching": "planning",
            "planning": "building",
            "building": "deploying",
            "deploying": "operating",
        }
        next_stage = stage_map.get(current_round)
        if next_stage:
            return [{"type": "stage_change", "stage": next_stage}]
        return None

    if et == EventType.ERROR:
        return [{
            "type": "error",
            "message": d.get("error", "Unknown error"),
            "agentId": d.get("agent_id", ""),
            "fatal": d.get("fatal", False),
        }]

    if et == EventType.SIMULATION_COMPLETED:
        msgs = []
        for aid in ["product", "tech", "ops", "finance"]:
            msgs.append({
                "type": "agent_complete",
                "agentId": aid,
                "summary": "Simulation complete",
            })
        msgs.append({"type": "stage_change", "stage": "complete"})
        return msgs

    return None


async def _send_loop(
    ws: WebSocket,
    queue: asyncio.Queue,
) -> None:
    """Push events from the event bus to the WebSocket client.

    This is the primary lifecycle controller — it runs until
    SIMULATION_COMPLETED arrives or the WebSocket disconnects.
    """
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=120.0)
        except asyncio.TimeoutError:
            # Keep the connection alive during long Claude API calls
            await ws.send_text(json.dumps({"type": "keepalive"}))
            continue

        messages = translate_event(event)
        if messages:
            for msg in messages:
                await ws.send_text(json.dumps(msg))
                # Voice synthesis for key events
                should_voice, voice_text = should_voice_event(msg["type"], msg)
                if should_voice:
                    audio_b64 = await synthesize_for_agent(
                        voice_text, msg.get("agentName", "narrator"),
                    )
                    if audio_b64:
                        await ws.send_text(json.dumps({
                            "type": "audio_narration",
                            "audio_base64": audio_b64,
                            "content_type": "audio/mpeg",
                            "text": voice_text,
                            "agentName": msg.get("agentName", "narrator"),
                        }))

        if event.event_type == EventType.SIMULATION_COMPLETED:
            return


async def _recv_loop(ws: WebSocket, session) -> None:
    """Receive user decisions from the WebSocket client.

    Runs independently — its exit does NOT affect the simulation.
    Catches all exceptions so cancellation is clean.
    """
    while True:
        try:
            raw = await ws.receive_text()
            data = json.loads(raw)
            if data.get("type") == "decision":
                proposal_id = getattr(session, "_current_proposal_id", None)
                if proposal_id and session.orchestrator:
                    await session.orchestrator.resolve_ceo_decision(
                        proposal_id=proposal_id,
                        approved=data.get("approved", False),
                        note=data.get("reason", ""),
                    )
            elif data.get("type") == "stop_simulation":
                session.status = "stopping"
        except (WebSocketDisconnect, asyncio.CancelledError):
            return
        except Exception:
            continue


@ws_router.websocket("/ws/simulation")
async def websocket_simulation(ws: WebSocket):
    await ws.accept()

    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
        init = json.loads(raw)
        idea = init.get("idea", "")
        budget = float(init.get("budget", 1000))

        if not idea:
            await ws.send_text(json.dumps({"type": "error", "message": "No idea provided"}))
            await ws.close()
            return

        session = create_session(idea=idea, budget=budget)
        session.status = "running"

        # Subscribe BEFORE starting simulation so we catch all events
        sub_id, queue = session.event_bus.subscribe()

        # Start simulation as a background task
        sim_task = asyncio.create_task(run_simulation(session))

        # Start recv_loop independently — it only forwards user decisions
        recv_task = asyncio.create_task(_recv_loop(ws, session))

        # send_loop is the primary lifecycle: runs until SIMULATION_COMPLETED
        try:
            await _send_loop(ws, queue)
        finally:
            recv_task.cancel()
            session.event_bus.unsubscribe(sub_id)
            if not sim_task.done():
                sim_task.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
