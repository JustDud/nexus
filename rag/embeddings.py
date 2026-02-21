"""Thin wrapper around embedding API. Swap internals to change providers."""

from google import genai
from google.genai import types

from config import get_settings


class EmbeddingProvider:
    """Wraps the Gemini embedding API for document and query embeddings."""

    def __init__(self):
        s = get_settings()
        self.client = genai.Client(api_key=s.gemini_api_key)
        self.model = s.embedding_model
        self.dimensions = s.embedding_dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts for document storage."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.dimensions,
            ),
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string for retrieval."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.dimensions,
            ),
        )
        return result.embeddings[0].values
