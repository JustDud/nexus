"""FastAPI router for ElevenLabs text-to-speech endpoints."""

import base64
from functools import lru_cache

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from config import get_settings
from integrations.elevenlabs.schemas import (
    ElevenLabsSynthesisRequest,
    ElevenLabsSynthesisResponse,
)
from integrations.elevenlabs.service import ElevenLabsError, ElevenLabsService

elevenlabs_router = APIRouter(tags=["elevenlabs"])


@lru_cache
def get_elevenlabs_service() -> ElevenLabsService | None:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        return None
    return ElevenLabsService(
        api_key=settings.elevenlabs_api_key,
        default_voice_id=settings.elevenlabs_voice_id,
        default_model_id=settings.elevenlabs_model_id,
        base_url=settings.elevenlabs_base_url,
    )


@elevenlabs_router.post(
    "/voice/elevenlabs/synthesize",
    response_model=ElevenLabsSynthesisResponse,
)
async def synthesize_text(req: ElevenLabsSynthesisRequest):
    service = get_elevenlabs_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ElevenLabs is not configured.",
        )

    try:
        result = await service.synthesize(
            text=req.text,
            voice_id=req.voice_id,
            model_id=req.model_id,
        )
    except ElevenLabsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ElevenLabsSynthesisResponse(
        audio_base64=base64.b64encode(result.audio_bytes).decode("ascii"),
        content_type=result.content_type,
        voice_id=result.voice_id,
        model_id=result.model_id,
    )


@elevenlabs_router.post("/voice/elevenlabs/synthesize/audio")
async def synthesize_text_audio(req: ElevenLabsSynthesisRequest):
    service = get_elevenlabs_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ElevenLabs is not configured.",
        )

    try:
        result = await service.synthesize(
            text=req.text,
            voice_id=req.voice_id,
            model_id=req.model_id,
        )
    except ElevenLabsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return Response(content=result.audio_bytes, media_type=result.content_type)
