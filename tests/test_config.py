"""Tests for configuration loading — no API keys needed for most tests."""

import os
import pytest
from functools import lru_cache


class TestSettingsClass:
    def test_settings_class_importable(self):
        from config import Settings
        assert Settings is not None

    def test_settings_has_all_expected_fields(self):
        from config import Settings
        fields = Settings.model_fields
        expected = [
            "anthropic_api_key",
            "gemini_api_key",
            "default_model",
            "embedding_model",
            "embedding_dimensions",
            "chunk_size",
            "chunk_overlap",
            "retrieval_top_k",
            "chroma_persist_dir",
            "chroma_collection_name",
            "stripe_secret_key",
            "stripe_publishable_key",
            "stripe_webhook_secret",
            "stripe_webhook_tolerance_seconds",
            "elevenlabs_api_key",
            "elevenlabs_voice_id",
            "elevenlabs_model_id",
            "elevenlabs_base_url",
        ]
        for field_name in expected:
            assert field_name in fields, f"Missing field: {field_name}"

    def test_settings_defaults(self):
        from config import Settings
        # Create with only required fields and disable .env loading for deterministic defaults.
        env_backup = {}
        env_keys = [
            "STRIPE_SECRET_KEY",
            "STRIPE_PUBLISHABLE_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_VOICE_ID",
            "ELEVENLABS_MODEL_ID",
            "ELEVENLABS_BASE_URL",
        ]
        for key in env_keys:
            env_backup[key] = os.environ.pop(key, None)

        try:
            s = Settings(
                anthropic_api_key="test",
                gemini_api_key="test",
                _env_file=None,
            )
            assert s.default_model == "claude-sonnet-4-6"
            assert s.embedding_model == "gemini-embedding-001"
            assert s.embedding_dimensions == 768
            assert s.chunk_size == 512
            assert s.chunk_overlap == 50
            assert s.retrieval_top_k == 5
            assert s.chroma_persist_dir == "./chroma_data"
            assert s.chroma_collection_name == "ghost_founder"
            assert s.stripe_secret_key is None
            assert s.stripe_publishable_key is None
            assert s.stripe_webhook_secret is None
            assert s.stripe_webhook_tolerance_seconds == 300
            assert s.elevenlabs_api_key is None
            assert s.elevenlabs_voice_id is None
            assert s.elevenlabs_model_id == "eleven_multilingual_v2"
            assert s.elevenlabs_base_url == "https://api.elevenlabs.io/v1"
        finally:
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_settings_override(self):
        from config import Settings
        s = Settings(
            anthropic_api_key="test",
            gemini_api_key="test",
            chunk_size=1024,
            retrieval_top_k=10,
        )
        assert s.chunk_size == 1024
        assert s.retrieval_top_k == 10

    def test_settings_fails_without_anthropic_key(self):
        from config import Settings
        # Clear env vars that might be set
        env_backup = {}
        for key in ["ANTHROPIC_API_KEY"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)
        try:
            with pytest.raises(Exception):
                Settings(_env_file=None)
        finally:
            os.environ.update(env_backup)

    def test_settings_from_env_vars(self):
        from config import Settings
        old_ant = os.environ.get("ANTHROPIC_API_KEY")
        old_oai = os.environ.get("GEMINI_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test123"
        os.environ["GEMINI_API_KEY"] = "gemini-test456"
        os.environ["CHUNK_SIZE"] = "256"
        try:
            s = Settings()
            assert s.anthropic_api_key == "sk-ant-test123"
            assert s.gemini_api_key == "gemini-test456"
            assert s.chunk_size == 256
        finally:
            # Restore original values (set by conftest)
            if old_ant is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_ant
            if old_oai is not None:
                os.environ["GEMINI_API_KEY"] = old_oai
            os.environ.pop("CHUNK_SIZE", None)


class TestGetSettings:
    def test_get_settings_is_callable(self):
        from config import get_settings
        assert callable(get_settings)

    def test_get_settings_is_cached(self):
        from config import get_settings
        # The function uses lru_cache, verify it's wrapped
        assert hasattr(get_settings, "cache_info")

    def test_get_settings_returns_settings_with_env(self):
        from config import get_settings, Settings
        # Clear the cache first
        get_settings.cache_clear()
        old_ant = os.environ.get("ANTHROPIC_API_KEY")
        old_oai = os.environ.get("GEMINI_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        os.environ["GEMINI_API_KEY"] = "test-key"
        try:
            s = get_settings()
            assert isinstance(s, Settings)
            assert s.anthropic_api_key == "test-key"
        finally:
            # Restore originals and re-cache with them
            if old_ant is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_ant
            if old_oai is not None:
                os.environ["GEMINI_API_KEY"] = old_oai
            get_settings.cache_clear()
