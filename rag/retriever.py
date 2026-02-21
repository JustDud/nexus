"""
Vector search retriever with optional domain filtering.
"""

import chromadb

from config import get_settings
from rag.embeddings import EmbeddingProvider


class Retriever:
    def __init__(self):
        s = get_settings()
        self.embedder = EmbeddingProvider()
        self.chroma_client = chromadb.PersistentClient(path=s.chroma_persist_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=s.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query: str,
        domain: str | None = None,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Search the vector store for relevant chunks.

        Args:
            query: The search query.
            domain: If set, only return chunks from this domain.
                    If None, search all domains.
            top_k: Number of results to return.

        Returns:
            List of dicts with keys: text, source_file, domain, score.
        """
        k = top_k or get_settings().retrieval_top_k
        query_vector = self.embedder.embed_query(query)

        where_filter = {"domain": domain} if domain else None

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Flatten ChromaDB's nested list format
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
                chunks.append(
                    {
                        "text": doc,
                        "source_file": meta.get("source_file", "unknown"),
                        "domain": meta.get("domain", "unknown"),
                        "chunk_index": meta.get("chunk_index", 0),
                        "score": 1 - distance if distance is not None else None,
                    }
                )

        return chunks
