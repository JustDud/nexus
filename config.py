from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API keys
    anthropic_api_key: str
    openai_api_key: str

    # Model settings
    default_model: str = "claude-sonnet-4-6"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # RAG settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "ghost_founder"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
