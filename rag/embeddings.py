from google import genai

from config import get_settings


class EmbeddingProvider:
    """Thin wrapper around Google Gemini embedding API."""

    def __init__(self):
        s = get_settings()
        self.client = genai.Client(api_key=s.gemini_api_key)
        self.model = s.embedding_model
        self.dimensions = s.embedding_dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of vectors."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config={"output_dimensionality": self.dimensions},
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self.embed([text])[0]
