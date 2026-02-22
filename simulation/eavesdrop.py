"""Eavesdrop — condensed per-agent debate audio with alternating voices.

When the user activates eavesdrop mode, this module listens for debate round
completions, condenses each agent's position via Gemini Flash, then synthesizes
each agent individually using two alternating ElevenLabs voices so the user
can hear distinct speakers arguing back and forth.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from fastapi import WebSocket
from google import genai
from google.genai import types

from config import get_settings
from simulation.events import EventBus, EventType
from simulation.voice import synthesize_for_agent

logger = logging.getLogger(__name__)

# Two ElevenLabs voice IDs for alternating speakers
_VOICE_A = "CwhRBWXzGAHq8TQ4Fs17"
_VOICE_B = "FGY2WhTYpPnrIDTdsKH5"

_CONDENSE_SYSTEM = """\
Condense each agent's debate stance into a punchy spoken soundbite.
For each agent, output EXACTLY one line:
[Agent Name]: [max 10 words, first person, opinionated]

Examples of good output:
Tech Lead: We can build this in two weeks, easy.
Finance: That burns half our runway, absolutely not.
Risk Officer: Legal exposure here is way too high.

One line per agent. No blank lines. No extra text."""


class EavesdropManager:
    """Generate per-agent condensed debate audio with alternating voices."""

    def __init__(self, event_bus: EventBus, ws: WebSocket, ws_lock: asyncio.Lock | None = None) -> None:
        self._event_bus = event_bus
        self._ws = ws
        self._active = False
        self._lock = ws_lock or asyncio.Lock()
        self._client: genai.Client | None = None
        self._model: str = "gemini-2.5-flash"

        settings = get_settings()
        if settings.gemini_api_key:
            self._client = genai.Client(api_key=settings.gemini_api_key)
            self._model = settings.narrator_gemini_model

    @property
    def is_active(self) -> bool:
        return self._active

    def activate(self) -> None:
        logger.info("Eavesdrop activated")
        self._active = True

    def deactivate(self) -> None:
        logger.info("Eavesdrop deactivated")
        self._active = False

    async def process_debate_round(self, round_num: int) -> None:
        """Generate and send per-agent eavesdrop audio for a completed debate round."""
        if not self._active or self._client is None:
            return

        # Gather agent positions from event history
        speaking_events = [
            e for e in self._event_bus.history
            if e.event_type == EventType.AGENT_SPEAKING
            and e.data.get("round") == round_num
        ]

        if not speaking_events:
            logger.warning("Eavesdrop: no AGENT_SPEAKING events for round %d", round_num)
            return

        logger.info("Eavesdrop: found %d speaking events for round %d", len(speaking_events), round_num)

        # Build condensation prompt
        positions = []
        for e in speaking_events:
            name = e.data.get("agent_name", "Agent")
            content = e.data.get("content", "")[:500]
            positions.append(f"{name}:\n{content}")

        prompt = (
            f"Debate round {round_num}. Condense each agent's position:\n\n"
            + "\n\n---\n\n".join(positions)
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_CONDENSE_SYSTEM,
                    max_output_tokens=150,
                    temperature=0.7,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            dialogue_text = response.text
            if not dialogue_text:
                return
        except Exception as e:
            logger.warning("Eavesdrop condensation failed: %s", e)
            return

        # Parse individual agent lines
        lines = _parse_agent_lines(dialogue_text.strip())
        if not lines:
            logger.warning("Eavesdrop: no agent lines parsed from: %s", dialogue_text[:200])
            return

        logger.info("Eavesdrop: synthesizing %d agent lines in parallel", len(lines))

        # Synthesize all agent lines in parallel
        async def _synth(i: int, agent_name: str, line_text: str) -> tuple[int, str, str, str | None]:
            voice_id = _VOICE_A if i % 2 == 0 else _VOICE_B
            audio_b64 = await synthesize_for_agent(line_text, agent_name, voice_id=voice_id)
            return (i, agent_name, line_text, audio_b64)

        results = await asyncio.gather(
            *(_synth(i, name, text) for i, (name, text) in enumerate(lines)),
            return_exceptions=True,
        )

        # Send audio in order, skipping failures
        for result in sorted(
            (r for r in results if isinstance(r, tuple)),
            key=lambda r: r[0],
        ):
            _, agent_name, line_text, audio_b64 = result
            if not audio_b64 or not self._active:
                continue
            try:
                async with self._lock:
                    await self._ws.send_text(json.dumps({
                        "type": "audio_eavesdrop",
                        "audio_base64": audio_b64,
                        "content_type": "audio/mpeg",
                        "text": line_text,
                        "agentName": agent_name,
                        "round": round_num,
                    }))
            except Exception as e:
                logger.warning("Eavesdrop WS send failed: %s", e)
                break


def _parse_agent_lines(text: str) -> list[tuple[str, str]]:
    """Parse 'Agent Name: their line' format into (name, full_line) pairs."""
    results: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(.+?):\s*(.+)$", line)
        if match:
            name = match.group(1).strip()
            content = match.group(2).strip()
            # Include agent name in spoken text for clarity
            results.append((name, f"{name} says: {content}"))
    return results
