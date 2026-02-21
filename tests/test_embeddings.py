"""Tests for the embedding provider — structural tests only, no live API calls."""

# conftest.py sets dummy API keys before this module loads.

from rag.embeddings import EmbeddingProvider


class TestEmbeddingProviderStructure:
    def test_provider_instantiates(self):
        provider = EmbeddingProvider()
        assert provider is not None

    def test_provider_has_embed_method(self):
        provider = EmbeddingProvider()
        assert hasattr(provider, "embed")
        assert callable(provider.embed)

    def test_provider_has_embed_query_method(self):
        provider = EmbeddingProvider()
        assert hasattr(provider, "embed_query")
        assert callable(provider.embed_query)

    def test_provider_uses_configured_model(self):
        provider = EmbeddingProvider()
        assert provider.model == "text-embedding-3-small"

    def test_provider_has_dimensions(self):
        provider = EmbeddingProvider()
        assert provider.dimensions == 1536

    def test_provider_has_openai_client(self):
        provider = EmbeddingProvider()
        assert provider.client is not None
