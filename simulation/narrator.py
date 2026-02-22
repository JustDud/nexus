"""Secretary narrator — generates contextual voice narration for simulation events.

Subscribes to the EventBus, filters for meaningful events, generates narration
text via Gemini Flash, synthesizes speech via ElevenLabs, and pushes audio to
the WebSocket client.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from fastapi import WebSocket
from google import genai
from google.genai import types

from config import get_settings
from simulation.events import EventBus, EventType, SimulationEvent
from simulation.voice import synthesize_for_agent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Narration event (intermediate representation)
# ---------------------------------------------------------------------------

@dataclass
class NarrationEvent:
    narration_type: str  # phase_transition | agent_activity | debate_summary | decision_moment | bookend
    context: dict
    priority: int  # 1 = high, 2 = medium


# ---------------------------------------------------------------------------
# Filter — decides which simulation events deserve narration
# ---------------------------------------------------------------------------

class NarrationFilter:
    """Evaluate SimulationEvents and produce NarrationEvents for the narrator."""

    def evaluate(self, event: SimulationEvent, history: list[SimulationEvent]) -> NarrationEvent | None:
        handler = {
            EventType.SIMULATION_STARTED: self._sim_started,
            EventType.SIMULATION_COMPLETED: self._sim_completed,
            EventType.PHASE_CHANGED: self._phase_changed,
            # AGENT_RESPONSE deliberately excluded — fires per agent, causes backlog
            EventType.DEBATE_ROUND_COMPLETE: self._debate_round,
            EventType.CONSENSUS_REACHED: self._consensus,
            EventType.DECISION_NEEDED: self._decision_needed,
            EventType.DECISION_MADE: self._decision_made,
        }.get(event.event_type)

        if handler is None:
            return None
        return handler(event, history)

    # -- handlers ----------------------------------------------------------

    @staticmethod
    def _sim_started(event: SimulationEvent, _h: list) -> NarrationEvent:
        return NarrationEvent(
            narration_type="bookend",
            context={"moment": "start", "idea": event.data.get("idea", "a new startup")},
            priority=1,
        )

    @staticmethod
    def _sim_completed(event: SimulationEvent, _h: list) -> NarrationEvent:
        return NarrationEvent(
            narration_type="bookend",
            context={
                "moment": "end",
                "status": event.data.get("status", "completed"),
                "total_spent": event.data.get("total_spent", 0),
            },
            priority=1,
        )

    @staticmethod
    def _phase_changed(event: SimulationEvent, _h: list) -> NarrationEvent | None:
        phase = event.data.get("phase", "")
        if not phase:
            return None
        return NarrationEvent(
            narration_type="phase_transition",
            context={"phase": phase},
            priority=1,
        )

    @staticmethod
    def _debate_round(event: SimulationEvent, history: list[SimulationEvent]) -> NarrationEvent:
        round_num = event.data.get("round", 0)
        speaking = [
            e for e in history
            if e.event_type == EventType.AGENT_SPEAKING and e.data.get("round") == round_num
        ]
        positions: list[str] = []
        for e in speaking:
            name = e.data.get("agent_name", "Agent")
            snippet = e.data.get("content", "")[:100]
            positions.append(f"{name}: {snippet}")
        return NarrationEvent(
            narration_type="debate_summary",
            context={"round": round_num, "positions": "; ".join(positions) or "No positions recorded."},
            priority=2,
        )

    @staticmethod
    def _consensus(event: SimulationEvent, _h: list) -> NarrationEvent:
        return NarrationEvent(
            narration_type="debate_summary",
            context={
                "round": event.data.get("round", 0),
                "consensus": True,
                "proposals": event.data.get("proposals", []),
            },
            priority=1,
        )

    @staticmethod
    def _decision_needed(event: SimulationEvent, _h: list) -> NarrationEvent:
        return NarrationEvent(
            narration_type="decision_moment",
            context={
                "action": "needed",
                "title": event.data.get("title", "a proposal"),
                "cost": event.data.get("cost", 0),
                "agent_name": event.data.get("agent_name", "An agent"),
            },
            priority=1,
        )

    @staticmethod
    def _decision_made(event: SimulationEvent, _h: list) -> NarrationEvent:
        return NarrationEvent(
            narration_type="decision_moment",
            context={
                "action": "resolved",
                "approved": event.data.get("approved", False),
            },
            priority=1,
        )


# ---------------------------------------------------------------------------
# Generator — produces narration text via Gemini Flash
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a professional narrator for a startup simulation. \
Describe what is happening in exactly ONE short sentence (under 20 words). \
Use a calm, documentary-style tone. Speak in present tense. \
Do NOT use quotation marks, agent dialogue, or bullet points."""

_PROMPT_TEMPLATES: dict[str, str] = {
    "bookend": "The simulation is {moment}ing. {extra}Describe this moment briefly.",
    "phase_transition": "The simulation transitions to the {phase} phase. Describe this transition.",
    "debate_summary": "Debate round {round} has concluded. Positions: {positions} Summarize the round.",
    "decision_moment": "{detail}",
}


def _build_prompt(narration: NarrationEvent) -> str:
    """Build a prompt string from a NarrationEvent."""
    ctx = dict(narration.context)
    ntype = narration.narration_type

    if ntype == "bookend":
        moment = ctx.get("moment", "start")
        if moment == "start":
            ctx["extra"] = f"The idea: {ctx.get('idea', '')}. "
        else:
            ctx["extra"] = f"Status: {ctx.get('status', 'completed')}. Total spent: ${ctx.get('total_spent', 0):,.0f}. "
        ctx["moment"] = moment

    elif ntype == "decision_moment":
        action = ctx.get("action", "needed")
        if action == "needed":
            ctx["detail"] = (
                f"{ctx.get('agent_name', 'An agent')} proposes: {ctx.get('title', 'a proposal')}, "
                f"costing ${ctx.get('cost', 0):,.0f}. The CEO must decide. Describe this moment."
            )
        else:
            outcome = "approved" if ctx.get("approved") else "rejected"
            ctx["detail"] = f"The CEO has {outcome} the proposal. Describe the outcome."

    elif ntype == "debate_summary" and ctx.get("consensus"):
        proposals = ctx.get("proposals", [])
        ctx["positions"] = f"Consensus reached on: {', '.join(proposals)}." if proposals else "Consensus reached."

    template = _PROMPT_TEMPLATES.get(ntype, "Describe what just happened in the simulation.")
    try:
        return template.format(**ctx)
    except KeyError:
        return template


class NarrationGenerator:
    """Generate narration text using Gemini Flash."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(self, narration: NarrationEvent) -> str | None:
        prompt = _build_prompt(narration)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    max_output_tokens=80,
                    temperature=0.7,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            text = response.text
            return text.strip() if text else None
        except Exception as e:
            logger.warning("Gemini narration generation failed: %s", e)
            return None


# ---------------------------------------------------------------------------
# Narrator — main loop tying filter + generator + TTS together
# ---------------------------------------------------------------------------

class SimulationNarrator:
    """Subscribe to EventBus events, narrate meaningful ones via voice."""

    def __init__(self, event_bus: EventBus, ws: WebSocket) -> None:
        self._event_bus = event_bus
        self._ws = ws
        self._filter = NarrationFilter()
        self._generator: NarrationGenerator | None = None
        self._lock = asyncio.Lock()
        self._pending_tasks: set[asyncio.Task] = set()
        self._eavesdrop_active = False
        self._narrating = False  # True while a narration is being generated/spoken

        settings = get_settings()
        if not settings.narrator_enabled:
            return
        if settings.gemini_api_key:
            self._generator = NarrationGenerator(
                api_key=settings.gemini_api_key,
                model=settings.narrator_gemini_model,
            )

    async def run(self, queue: asyncio.Queue) -> None:
        """Consume events from queue and narrate meaningful ones."""
        if self._generator is None:
            # Drain queue silently — keeps EventBus subscriber from backing up
            while True:
                event = await queue.get()
                if event.event_type == EventType.SIMULATION_COMPLETED:
                    return

        while True:
            event = await queue.get()

            if event.event_type == EventType.SIMULATION_COMPLETED:
                # Wait for any in-flight narrations to finish before final one
                if self._pending_tasks:
                    await asyncio.gather(*self._pending_tasks, return_exceptions=True)
                    self._pending_tasks.clear()
                await self._maybe_narrate(event)
                return

            # Fire-and-forget so we don't block the queue consumer
            task = asyncio.create_task(self._maybe_narrate(event))
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)

    def pause_for_eavesdrop(self) -> None:
        """Suppress narration while the user is eavesdropping on agents."""
        self._eavesdrop_active = True

    def resume_from_eavesdrop(self) -> None:
        """Resume narration after eavesdrop ends."""
        self._eavesdrop_active = False

    async def _maybe_narrate(self, event: SimulationEvent) -> None:
        if self._eavesdrop_active:
            return
        narration = self._filter.evaluate(event, self._event_bus.history)
        if narration is None or self._generator is None:
            return

        # Skip low-priority narrations if already busy to prevent audio pile-up
        if self._narrating and narration.priority >= 2:
            return

        self._narrating = True
        try:
            text = await self._generator.generate(narration)
            if not text:
                return

            audio_b64 = await synthesize_for_agent(text, "narrator")
            if audio_b64:
                # Serialize only the WS send to avoid interleaved writes
                async with self._lock:
                    await self._ws.send_text(json.dumps({
                        "type": "audio_narration",
                        "audio_base64": audio_b64,
                        "content_type": "audio/mpeg",
                        "text": text,
                        "agentName": "narrator",
                    }))
        except Exception as e:
            logger.warning("Narration failed: %s", e)
        finally:
            self._narrating = False
