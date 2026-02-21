import httpx
from openai import OpenAI

from config import get_settings


class EmbeddingProvider:
    """Embedding provider wrapper with provider switching via config."""

    def __init__(self):
        s = get_settings()
        self.provider = s.embedding_provider.lower().strip()
        self.dimensions = s.embedding_dimensions
        self.client = None

        if self.provider == "openai":
            self.client = OpenAI(api_key=s.openai_api_key)
            self.model = s.embedding_model
        elif self.provider == "gemini":
            if not s.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini.")
            self.model = s.gemini_embedding_model
            self._gemini_api_key = s.gemini_api_key
            self._gemini_base_url = s.gemini_base_url.rstrip("/")
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def _embed_gemini_text(self, text: str, task_type: str | None = None) -> list[float]:
        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"{self._gemini_base_url}/{model_path}:embedContent"
        params = {"key": self._gemini_api_key}
        payload: dict = {"content": {"parts": [{"text": text}]}}
        if task_type:
            payload["taskType"] = task_type

        response = httpx.post(url, params=params, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        values = data.get("embedding", {}).get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("Gemini embedding response missing 'embedding.values'.")
        return values

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of vectors."""
        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )
            return [item.embedding for item in response.data]

        return [self._embed_gemini_text(text=t, task_type="RETRIEVAL_DOCUMENT") for t in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        if self.provider == "gemini":
            return self._embed_gemini_text(text=text, task_type="RETRIEVAL_QUERY")
        return self.embed([text])[0]
