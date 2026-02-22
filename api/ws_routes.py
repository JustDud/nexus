"""WebSocket endpoint for real-time simulation streaming."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai

from config import get_settings
from simulation.eavesdrop import EavesdropManager
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
        return [
            {
                "type": "agent_thinking",
                "agentId": agent_id,
                "fragments": sentences if sentences else ["Processing..."],
            },
            {
                "type": "agent_acting",
                "agentId": agent_id,
                "action": content,
            },
        ]

    if et == EventType.AGENT_SPEAKING:
        agent_id = d.get("agent_id", "tech")
        content = d.get("content", "")
        sentences = [s.strip() for s in content.split(".") if s.strip()][:3]
        return [
            {
                "type": "agent_thinking",
                "agentId": agent_id,
                "fragments": sentences if sentences else ["Debating..."],
            },
            {
                "type": "agent_acting",
                "agentId": agent_id,
                "action": content,
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

    if et == EventType.DEBATE_STARTED:
        return [{"type": "debate_started", "topic": d.get("topic", "")}]

    if et == EventType.DEBATE_ENDED:
        return [{"type": "debate_ended"}]

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


async def _ws_send(ws: WebSocket, data: str, ws_lock: asyncio.Lock) -> None:
    """Send text over WebSocket with a shared lock to prevent concurrent writes."""
    async with ws_lock:
        await ws.send_text(data)


async def _send_loop(
    ws: WebSocket,
    queue: asyncio.Queue,
    ws_lock: asyncio.Lock,
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
            await _ws_send(ws, json.dumps({"type": "keepalive"}), ws_lock)
            continue

        messages = translate_event(event)
        if messages:
            for msg in messages:
                await _ws_send(ws, json.dumps(msg), ws_lock)

        if event.event_type == EventType.SIMULATION_COMPLETED:
            return


async def _recv_loop(
    ws: WebSocket,
    session,
    eavesdrop: EavesdropManager,
) -> None:
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
                sim_task = getattr(session, "_sim_task", None)
                if sim_task and not sim_task.done():
                    sim_task.cancel()
            elif data.get("type") == "eavesdrop_start":
                logger.info("Received eavesdrop_start from client")
                eavesdrop.activate()
            elif data.get("type") == "eavesdrop_stop":
                logger.info("Received eavesdrop_stop from client")
                eavesdrop.deactivate()
        except (WebSocketDisconnect, asyncio.CancelledError):
            return
        except Exception:
            continue


async def _eavesdrop_loop(
    eavesdrop: EavesdropManager,
    queue: asyncio.Queue,
) -> None:
    """Listen for debate round completions and generate eavesdrop audio.

    Processing is fire-and-forget so the loop stays responsive to new events.
    """
    processing_tasks: set[asyncio.Task] = set()

    while True:
        event = await queue.get()
        if event.event_type == EventType.SIMULATION_COMPLETED:
            # Wait for any in-flight eavesdrop processing to finish
            if processing_tasks:
                await asyncio.gather(*processing_tasks, return_exceptions=True)
            return
        if event.event_type == EventType.DEBATE_ENDED:
            if eavesdrop.is_active:
                logger.info("Eavesdrop: debate ended, deactivating")
                eavesdrop.deactivate()
        if event.event_type == EventType.DEBATE_ROUND_COMPLETE:
            round_num = event.data.get("round", 0)
            if eavesdrop.is_active:
                logger.info("Eavesdrop: fire-and-forget processing round %d", round_num)
                task = asyncio.create_task(
                    _safe_process_round(eavesdrop, round_num)
                )
                processing_tasks.add(task)
                task.add_done_callback(processing_tasks.discard)
            else:
                logger.debug("Eavesdrop: round %d skipped (not active)", round_num)


async def _safe_process_round(eavesdrop: EavesdropManager, round_num: int) -> None:
    """Wrap process_debate_round with exception handling."""
    try:
        await eavesdrop.process_debate_round(round_num)
    except Exception as e:
        logger.warning("Eavesdrop processing failed for round %d: %s", round_num, e)


async def _generate_project_title(idea: str, ws: WebSocket, ws_lock: asyncio.Lock) -> None:
    """Use Gemini Flash to generate a short project codename, send it over WS."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "Generate a short, punchy project codename (2-4 words max) for this startup idea. "
                "Reply with ONLY the codename, nothing else. No quotes, no punctuation.\n\n"
                f"Idea: {idea[:500]}"
            ),
            config=genai.types.GenerateContentConfig(
                max_output_tokens=20,
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
            ),
        )
        title = resp.text.strip().strip('"\'').strip()
        if title:
            await _ws_send(ws, json.dumps({"type": "project_title", "title": title}), ws_lock)
    except Exception as e:
        logger.warning("Failed to generate project title: %s", e)


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

        # Shared lock — all WebSocket writes must go through this
        ws_lock = asyncio.Lock()

        # Subscribe BEFORE starting simulation so we catch all events
        sub_id, queue = session.event_bus.subscribe()

        # Eavesdrop gets its own subscriber for debate round events
        eavesdrop_sub_id, eavesdrop_queue = session.event_bus.subscribe()
        eavesdrop = EavesdropManager(event_bus=session.event_bus, ws=ws, ws_lock=ws_lock)
        eavesdrop_task = asyncio.create_task(
            _eavesdrop_loop(eavesdrop, eavesdrop_queue)
        )

        # Generate project title concurrently (fire-and-forget)
        asyncio.create_task(_generate_project_title(idea, ws, ws_lock))

        # Start simulation as a background task
        sim_task = asyncio.create_task(run_simulation(session))
        session._sim_task = sim_task

        # Start recv_loop independently — it only forwards user decisions
        recv_task = asyncio.create_task(
            _recv_loop(ws, session, eavesdrop)
        )

        # send_loop is the primary lifecycle: runs until SIMULATION_COMPLETED
        try:
            await _send_loop(ws, queue, ws_lock)
        finally:
            recv_task.cancel()
            eavesdrop_task.cancel()
            session.event_bus.unsubscribe(sub_id)
            session.event_bus.unsubscribe(eavesdrop_sub_id)
            if not sim_task.done():
                sim_task.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
