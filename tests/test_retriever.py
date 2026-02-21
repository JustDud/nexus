"""Tests for the retriever — uses a real ChromaDB in-memory/temp dir, no external API calls."""

# conftest.py sets dummy API keys before this module loads.

import pytest

import chromadb


class TestRetrieverStructure:
    def test_retriever_importable(self):
        from rag.retriever import Retriever
        assert Retriever is not None

    def test_retriever_has_search_method(self):
        from rag.retriever import Retriever
        assert hasattr(Retriever, "search")
        assert callable(Retriever.search)


class TestRetrieverSearchLogic:
    """Test the search logic using ChromaDB directly (bypasses embedding API)."""

    # Deterministic low-dimensional vectors keep tests self-contained and
    # avoid default ONNX model downloads in restricted environments.
    VECTORS = {
        "market": [1.0, 0.0, 0.0],
        "tech": [0.0, 1.0, 0.0],
        "finance": [0.0, 0.0, 1.0],
        "pet": [0.95, 0.05, 0.0],
        "query_market": [0.99, 0.01, 0.0],
        "query_pet": [0.97, 0.03, 0.0],
        "query_generic": [0.5, 0.5, 0.0],
    }

    def _make_collection(self, tmp_dir):
        """Create a test collection with pre-embedded data."""
        client = chromadb.PersistentClient(path=tmp_dir)
        collection = client.get_or_create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"},
        )
        return client, collection

    def test_chromadb_basic_add_and_query(self, tmp_path):
        """Verify ChromaDB itself works — add docs, query them back."""
        _, collection = self._make_collection(str(tmp_path))

        collection.add(
            ids=["doc1", "doc2", "doc3"],
            documents=["The pet health market is worth $300B",
                        "React and Vite are popular frontend tools",
                        "Burn rate should be monitored weekly"],
            embeddings=[
                self.VECTORS["market"],
                self.VECTORS["tech"],
                self.VECTORS["finance"],
            ],
            metadatas=[
                {"domain": "market", "source_file": "report.pdf", "chunk_index": 0},
                {"domain": "tech", "source_file": "stack.md", "chunk_index": 0},
                {"domain": "finance", "source_file": "guide.txt", "chunk_index": 0},
            ],
        )

        assert collection.count() == 3

        # Query without filter
        results = collection.query(
            query_embeddings=[self.VECTORS["query_market"]],
            n_results=2,
            include=["documents", "metadatas", "distances"],
        )
        assert len(results["documents"][0]) == 2

    def test_chromadb_domain_filter(self, tmp_path):
        """Verify metadata filtering works for domain isolation."""
        _, collection = self._make_collection(str(tmp_path))

        collection.add(
            ids=["m1", "t1", "f1"],
            documents=["Market data here", "Tech stack info", "Financial projections"],
            embeddings=[
                self.VECTORS["market"],
                self.VECTORS["tech"],
                self.VECTORS["finance"],
            ],
            metadatas=[
                {"domain": "market", "source_file": "a.txt", "chunk_index": 0},
                {"domain": "tech", "source_file": "b.txt", "chunk_index": 0},
                {"domain": "finance", "source_file": "c.txt", "chunk_index": 0},
            ],
        )

        # Filter by domain
        results = collection.query(
            query_embeddings=[self.VECTORS["query_generic"]],
            n_results=10,
            where={"domain": "market"},
            include=["documents", "metadatas"],
        )
        assert len(results["documents"][0]) == 1
        assert results["metadatas"][0][0]["domain"] == "market"

    def test_chromadb_empty_collection_query(self, tmp_path):
        """Query on empty collection should return empty results."""
        _, collection = self._make_collection(str(tmp_path))

        results = collection.query(
            query_embeddings=[self.VECTORS["query_generic"]],
            n_results=5,
            include=["documents"],
        )
        assert results["documents"][0] == []

    def test_chromadb_persistence(self, tmp_path):
        """Data should persist after client is recreated."""
        path = str(tmp_path)

        # First client: add data
        client1 = chromadb.PersistentClient(path=path)
        coll1 = client1.get_or_create_collection(name="persist_test")
        coll1.add(
            ids=["p1"],
            documents=["Persistent data"],
            embeddings=[self.VECTORS["market"]],
        )

        # Second client: read data back
        client2 = chromadb.PersistentClient(path=path)
        coll2 = client2.get_collection(name="persist_test")
        assert coll2.count() == 1

    def test_chromadb_upsert_overwrites(self, tmp_path):
        """Upsert should overwrite existing documents."""
        _, collection = self._make_collection(str(tmp_path))

        collection.add(
            ids=["dup1"],
            documents=["Original"],
            embeddings=[self.VECTORS["market"]],
        )
        assert collection.count() == 1

        # Upsert should overwrite
        collection.upsert(
            ids=["dup1"],
            documents=["Updated"],
            embeddings=[self.VECTORS["market"]],
        )
        assert collection.count() == 1
        results = collection.get(ids=["dup1"], include=["documents"])
        assert results["documents"][0] == "Updated"

    def test_chromadb_score_ordering(self, tmp_path):
        """More relevant documents should have lower distance."""
        _, collection = self._make_collection(str(tmp_path))

        collection.add(
            ids=["close", "far"],
            documents=[
                "The dog is sick and needs a veterinary checkup",
                "Financial quarterly report for Q3 2025",
            ],
            embeddings=[self.VECTORS["pet"], self.VECTORS["finance"]],
            metadatas=[
                {"domain": "test", "source_file": "a.txt", "chunk_index": 0},
                {"domain": "test", "source_file": "b.txt", "chunk_index": 0},
            ],
        )

        results = collection.query(
            query_embeddings=[self.VECTORS["query_pet"]],
            n_results=2,
            include=["documents", "distances"],
        )
        distances = results["distances"][0]
        docs = results["documents"][0]

        # The pet/vet document should be closer (lower distance)
        assert "dog" in docs[0] or "veterinary" in docs[0]
        assert distances[0] <= distances[1]
