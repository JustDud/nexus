"""Tests for ElevenLabs integration routes."""

import base64
import os

import pytest
from fastapi.testclient import TestClient

from config import get_settings
from integrations.elevenlabs.router import get_elevenlabs_service
from integrations.elevenlabs.service import ElevenLabsSynthesisResult
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class _FakeElevenLabsService:
    async def synthesize(self, text: str, voice_id: str | None = None, model_id: str | None = None):
        return ElevenLabsSynthesisResult(
            audio_bytes=b"fake-audio",
            content_type="audio/mpeg",
            voice_id=voice_id or "default-voice",
            model_id=model_id or "eleven_multilingual_v2",
        )


class TestElevenLabsRoutes:
    def teardown_method(self):
        get_settings.cache_clear()
        get_elevenlabs_service.cache_clear()
        os.environ.pop("ELEVENLABS_API_KEY", None)
        os.environ.pop("ELEVENLABS_VOICE_ID", None)

    def test_synthesize_not_configured_returns_503(self, client):
        get_settings.cache_clear()
        get_elevenlabs_service.cache_clear()
        os.environ["ELEVENLABS_API_KEY"] = ""

        resp = client.post("/api/voice/elevenlabs/synthesize", json={"text": "Hello world"})
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]

    def test_synthesize_returns_base64_audio(self, client, monkeypatch):
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        os.environ["ELEVENLABS_VOICE_ID"] = "voice-1"
        get_settings.cache_clear()
        get_elevenlabs_service.cache_clear()

        monkeypatch.setattr(
            "integrations.elevenlabs.router.get_elevenlabs_service",
            lambda: _FakeElevenLabsService(),
        )

        resp = client.post("/api/voice/elevenlabs/synthesize", json={"text": "Hello world"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["content_type"] == "audio/mpeg"
        assert body["voice_id"] == "default-voice"
        assert base64.b64decode(body["audio_base64"]) == b"fake-audio"

    def test_synthesize_audio_returns_binary(self, client, monkeypatch):
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        get_settings.cache_clear()
        get_elevenlabs_service.cache_clear()

        monkeypatch.setattr(
            "integrations.elevenlabs.router.get_elevenlabs_service",
            lambda: _FakeElevenLabsService(),
        )

        resp = client.post("/api/voice/elevenlabs/synthesize/audio", json={"text": "Hello world"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("audio/mpeg")
        assert resp.content == b"fake-audio"
