"""Voice synthesis helpers for simulation narration."""

import base64
import logging

logger = logging.getLogger(__name__)


async def synthesize_for_agent(
    text: str,
    agent_name: str,
    voice_id: str | None = None,
) -> str | None:
    """Synthesize speech. Returns base64-encoded audio or None if unavailable.

    If *voice_id* is provided it overrides the default ElevenLabs voice.
    """
    try:
        from integrations.elevenlabs.router import get_elevenlabs_service
    except ImportError:
        return None

    service = get_elevenlabs_service()
    if service is None:
        return None

    # Truncate long texts to control API costs
    if len(text) > 500:
        text = text[:497] + "..."

    try:
        result = await service.synthesize(text=text, voice_id=voice_id)
        return base64.b64encode(result.audio_bytes).decode("ascii")
    except Exception as e:
        logger.warning("Voice synthesis failed for %s: %s", agent_name, e)
        return None
