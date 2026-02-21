"""WebSocket endpoint for real-time simulation streaming."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from simulation.events import EventType, SimulationEvent
from simulation.orchestrator import run_simulation
from simulation.session import create_session

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

    if et == EventType.BUDGET_UPDATED:
        return [
            {
                "type": "transaction",
                "agentId": d.get("agent_id", "finance"),
                "description": d.get("description", "Expense"),
                "amount": d.get("amount", 0),
                "status": "approved" if d.get("approved") else "blocked",
            },
            {
                "type": "budget_update",
                "spent": d.get("spent", 0),
                "total": d.get("total", 0),
            },
        ]

    if et == EventType.ROUND_COMPLETED:
        stage_map = {
            "researching": "planning",
            "planning": "building",
            "building": "deploying",
            "deploying": "complete",
        }
        current = d.get("round", "")
        next_stage = stage_map.get(current)
        if next_stage:
            return [{"type": "stage_change", "stage": next_stage}]
        return None

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

        await session.event_bus.emit(SimulationEvent(
            event_type=EventType.SIMULATION_STARTED,
            data={"idea": idea, "budget": budget},
        ))

        sub_id, queue = session.event_bus.subscribe()
        task = asyncio.create_task(run_simulation(session))

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    await ws.send_text(json.dumps({"type": "keepalive"}))
                    continue

                messages = translate_event(event)
                if messages:
                    for msg in messages:
                        await ws.send_text(json.dumps(msg))

                if event.event_type == EventType.SIMULATION_COMPLETED:
                    break
        finally:
            session.event_bus.unsubscribe(sub_id)
            if not task.done():
                task.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
