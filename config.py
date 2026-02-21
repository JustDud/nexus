from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API keys
    anthropic_api_key: str
    openai_api_key: str | None = None
    gemini_api_key: str = ""

    # Model settings
    default_model: str = "claude-sonnet-4-6"
    embedding_provider: str = "gemini"  # openai | gemini
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    # RAG settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "ghost_founder"

    # Stripe
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_webhook_tolerance_seconds: int = 300

    # ElevenLabs
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"

    # Postgres / ingestion pipeline
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/ghost_founder"
    postgres_schema: str = "public"
    ingestion_user_agent: str = "GhostFounderBot/1.0"
    ingestion_request_timeout_seconds: int = 20
    ingestion_rate_limit_seconds: float = 0.5
    ingestion_max_retries: int = 2
    ingestion_clean_min_words: int = 40
    ingestion_clean_min_unique_words: int = 20
    ingestion_embedding_batch_size: int = 100
    ingestion_reindex_unchanged: bool = False
    ingestion_playwright_enabled: bool = False
    ingestion_playwright_min_html_chars: int = 1200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
