"""Voice synthesis for agent narration during simulation."""

import base64
import logging

logger = logging.getLogger(__name__)


async def synthesize_for_agent(text: str, agent_name: str) -> str | None:
    """Synthesize speech. Returns base64-encoded audio or None if unavailable."""
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
        result = await service.synthesize(text=text)
        return base64.b64encode(result.audio_bytes).decode("ascii")
    except Exception as e:
        logger.warning("Voice synthesis failed for %s: %s", agent_name, e)
        return None


def should_voice_event(msg_type: str, data: dict) -> tuple[bool, str]:
    """Determine if a frontend message should be voiced. Returns (should_voice, text)."""
    if msg_type == "approval_required":
        agent = data.get("agentName", "An agent")
        title = data.get("title", "a new proposal")
        cost = data.get("cost", 0)
        return True, f"{agent} proposes: {title}, costing ${cost:.0f}. Awaiting your approval."

    if msg_type == "approval_resolved":
        status = "approved" if data.get("approved") else "rejected"
        return True, f"The CEO has {status} the proposal."

    if msg_type == "stage_change":
        stage = data.get("stage", "")
        labels = {
            "planning": "Research complete. Moving to planning phase.",
            "building": "Planning complete. Moving to building phase.",
            "deploying": "Build complete. Moving to deployment.",
            "operating": "Deployment complete. Entering continuous operations.",
            "complete": "Simulation complete. Final report ready.",
        }
        text = labels.get(stage)
        return (True, text) if text else (False, "")

    if msg_type == "ops_round":
        r = data.get("round", 0)
        return True, f"Operations week {r} beginning."

    return False, ""
