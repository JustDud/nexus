from openai import OpenAI

from config import get_settings


class EmbeddingProvider:
    """Thin wrapper around an embedding API. Swap the internals to change providers."""

    def __init__(self):
        s = get_settings()
        self.client = OpenAI(api_key=s.openai_api_key)
        self.model = s.embedding_model
        self.dimensions = s.embedding_dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of vectors."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self.embed([text])[0]
