"""ElevenLabs text-to-speech service wrapper."""

from dataclasses import dataclass

import httpx


class ElevenLabsError(RuntimeError):
    """Raised for ElevenLabs request/configuration errors."""


@dataclass
class ElevenLabsSynthesisResult:
    audio_bytes: bytes
    content_type: str
    voice_id: str
    model_id: str


@dataclass
class ElevenLabsService:
    api_key: str
    default_voice_id: str | None
    default_model_id: str
    base_url: str = "https://api.elevenlabs.io/v1"
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ElevenLabsError("Missing ELEVENLABS_API_KEY.")

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> ElevenLabsSynthesisResult:
        resolved_voice_id = voice_id or self.default_voice_id
        if not resolved_voice_id:
            raise ElevenLabsError("Missing ElevenLabs voice_id.")

        resolved_model_id = model_id or self.default_model_id
        url = f"{self.base_url}/text-to-speech/{resolved_voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {"text": text, "model_id": resolved_model_id}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise ElevenLabsError(
                f"ElevenLabs request failed: {response.status_code} {response.text}"
            )

        return ElevenLabsSynthesisResult(
            audio_bytes=response.content,
            content_type=response.headers.get("content-type", "audio/mpeg"),
            voice_id=resolved_voice_id,
            model_id=resolved_model_id,
        )
