"""Eavesdrop — per-agent debate audio with alternating voices.

When the user activates eavesdrop mode, this module listens for debate round
completions, extracts a short soundbite from each agent's position, then
synthesizes each agent using two alternating ElevenLabs voices so the user
can hear distinct speakers arguing back and forth.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from simulation.events import EventBus, EventType
from simulation.voice import synthesize_for_agent

logger = logging.getLogger(__name__)

# Two ElevenLabs voice IDs for alternating speakers
_VOICE_A = "CwhRBWXzGAHq8TQ4Fs17"
_VOICE_B = "FGY2WhTYpPnrIDTdsKH5"

# Fastest ElevenLabs model for low-latency eavesdrop
_TURBO_MODEL = "eleven_turbo_v2_5"


def _extract_soundbite(text: str, max_words: int = 18) -> str:
    """Pull the first meaningful sentence from agent output, capped at max_words."""
    # Strip markdown / bullet noise per line, find first meaningful one
    lines = []
    for raw_line in text.split("\n"):
        line = re.sub(r"^[\s#*\->•]+", "", raw_line).strip()
        if len(line) < 10:
            continue
        m = re.match(r"^(PROPOSAL|COST|CATEGORY|REASON|VOTE|REASONING|CONDITIONS):\s*(.*)", line)
        if m:
            # Use the value after the prefix if it's long enough
            rest = m.group(2).strip()
            if len(rest) >= 10:
                line = rest
            else:
                continue
        lines.append(line)
        break  # first meaningful line only

    if not lines:
        return ""

    sentence = lines[0]
    # Truncate to max_words
    words = sentence.split()
    if len(words) > max_words:
        sentence = " ".join(words[:max_words]) + "..."
    return sentence


class EavesdropManager:
    """Generate per-agent debate audio with alternating voices."""

    def __init__(self, event_bus: EventBus, ws: WebSocket, ws_lock: asyncio.Lock | None = None) -> None:
        self._event_bus = event_bus
        self._ws = ws
        self._active = False
        self._lock = ws_lock or asyncio.Lock()

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
        if not self._active:
            return

        if self._ws.client_state != WebSocketState.CONNECTED:
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

        # Extract soundbites locally (no API call)
        lines: list[tuple[str, str]] = []
        for e in speaking_events:
            name = e.data.get("agent_name", "Agent")
            content = e.data.get("content", "")
            bite = _extract_soundbite(content)
            if bite:
                lines.append((name, f"{name} says: {bite}"))

        if not lines:
            return

        logger.info("Eavesdrop: synthesizing %d agents for round %d", len(lines), round_num)

        # Synthesize all agent lines in parallel with turbo model
        async def _synth(i: int, agent_name: str, line_text: str) -> tuple[int, str, str, str | None]:
            voice_id = _VOICE_A if i % 2 == 0 else _VOICE_B
            audio_b64 = await synthesize_for_agent(
                line_text, agent_name, voice_id=voice_id, model_id=_TURBO_MODEL,
            )
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
            if not audio_b64 or not self._active or self._ws.client_state != WebSocketState.CONNECTED:
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
