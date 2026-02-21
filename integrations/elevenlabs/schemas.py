"""Pydantic models for ElevenLabs API routes."""

from pydantic import BaseModel, Field


class ElevenLabsSynthesisRequest(BaseModel):
    text: str = Field(min_length=1)
    voice_id: str | None = None
    model_id: str | None = None


class ElevenLabsSynthesisResponse(BaseModel):
    audio_base64: str
    content_type: str
    voice_id: str
    model_id: str
