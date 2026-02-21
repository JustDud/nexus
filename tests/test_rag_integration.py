"""Integration tests for the RAG pipeline — chunking, storage, retrieval.

Uses real ChromaDB and real chunking but mocked embeddings to avoid API calls.
"""

import os
from pathlib import Path
from unittest.mock import patch

import chromadb
import pytest

from config import get_settings
from rag.chunker import chunk_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Simple deterministic embeddings: hash-based, 768-dim (matches Gemini config)
def _fake_embed(texts: list[str]) -> list[list[float]]:
    """Generate deterministic fake embeddings for testing."""
    vectors = []
    for text in texts:
        h = hash(text) % (2**32)
        # Create a sparse 768-dim vector seeded by hash
        vec = [0.0] * 768
        for i in range(768):
            vec[i] = ((h * (i + 1)) % 1000) / 1000.0
        # Normalize
        norm = sum(v * v for v in vec) ** 0.5
        vec = [v / norm for v in vec]
        vectors.append(vec)
    return vectors


def _fake_embed_single(text: str) -> list[float]:
    return _fake_embed([text])[0]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChunkingFixtures:
    """Verify fixture files are chunked correctly."""

    def test_market_data_chunks_within_limit(self):
        text = (FIXTURES_DIR / "market_data.txt").read_text()
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
        assert len(chunks) >= 2  # ~800 chars -> at least 2 chunks
        for chunk in chunks:
            assert len(chunk) <= 562  # 512 chunk_size + 50 overlap

    def test_tech_stack_chunks_within_limit(self):
        text = (FIXTURES_DIR / "tech_stack.txt").read_text()
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 562  # 512 chunk_size + 50 overlap

    def test_financials_chunks_within_limit(self):
        text = (FIXTURES_DIR / "financials.txt").read_text()
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 562  # 512 chunk_size + 50 overlap

    def test_no_empty_chunks(self):
        for fixture in FIXTURES_DIR.glob("*.txt"):
            text = fixture.read_text()
            chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
            for chunk in chunks:
                assert chunk.strip(), f"Empty chunk in {fixture.name}"


class TestStorageAndRetrieval:
    """Test ingestion into ChromaDB and retrieval with domain filtering."""

    def _setup_collection(self, tmp_path):
        """Ingest all fixtures into a temp ChromaDB collection."""
        client = chromadb.PersistentClient(path=str(tmp_path))
        collection = client.get_or_create_collection(
            name="test_rag", metadata={"hnsw:space": "cosine"}
        )

        domains = {
            "market_data.txt": "market",
            "tech_stack.txt": "tech",
            "financials.txt": "finance",
        }

        for fixture in FIXTURES_DIR.glob("*.txt"):
            domain = domains.get(fixture.name, "general")
            text = fixture.read_text()
            chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
            vectors = _fake_embed(chunks)

            ids = [f"{domain}_{fixture.stem}_{i}" for i in range(len(chunks))]
            metadatas = [
                {"domain": domain, "source_file": fixture.name, "chunk_index": i}
                for i in range(len(chunks))
            ]

            collection.add(
                ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas
            )

        return client, collection

    def test_all_chunks_stored(self, tmp_path):
        _, collection = self._setup_collection(tmp_path)
        # Should have chunks from all 3 files
        assert collection.count() >= 6  # At least 2 chunks per file

    def test_domain_filter_returns_only_matching(self, tmp_path):
        _, collection = self._setup_collection(tmp_path)

        query_vec = _fake_embed_single("pet health market size")
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=10,
            where={"domain": "market"},
            include=["documents", "metadatas"],
        )

        for meta in results["metadatas"][0]:
            assert meta["domain"] == "market"

    def test_top_k_respected(self, tmp_path):
        _, collection = self._setup_collection(tmp_path)

        query_vec = _fake_embed_single("technical architecture")
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=3,
            include=["documents"],
        )

        assert len(results["documents"][0]) <= 3

    def test_chunks_contain_source_metadata(self, tmp_path):
        _, collection = self._setup_collection(tmp_path)

        query_vec = _fake_embed_single("financial projections")
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=5,
            include=["metadatas"],
        )

        for meta in results["metadatas"][0]:
            assert "source_file" in meta
            assert "domain" in meta
            assert "chunk_index" in meta

    def test_retrieved_chunks_are_within_size_limit(self, tmp_path):
        _, collection = self._setup_collection(tmp_path)

        query_vec = _fake_embed_single("burn rate runway")
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=5,
            include=["documents"],
        )

        for doc in results["documents"][0]:
            assert len(doc) <= 562  # 512 chunk_size + 50 overlap
