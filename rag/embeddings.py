"""Thin wrapper around embedding API. Supports OpenAI and Gemini providers."""

from google import genai
from google.genai import types

from config import get_settings


class EmbeddingProvider:
    """Embedding provider wrapper with provider switching via config."""

    def __init__(self):
        s = get_settings()
        self.provider = s.embedding_provider.lower().strip()
        self.dimensions = s.embedding_dimensions
        self.client = None

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=s.openai_api_key)
            self.model = s.embedding_model
        elif self.provider == "gemini":
            if not s.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini.")
            self.client = genai.Client(api_key=s.gemini_api_key)
            self.model = s.gemini_embedding_model
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of vectors."""
        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )
            return [item.embedding for item in response.data]

        # Gemini path — use google-genai SDK
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
        """Embed a single query string."""
        if self.provider == "openai":
            return self.embed([text])[0]

        # Gemini path
        result = self.client.models.embed_content(
            model=self.model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.dimensions,
            ),
        )
        return result.embeddings[0].values
