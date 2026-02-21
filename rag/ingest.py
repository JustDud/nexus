"""
Document ingestion pipeline.
Loads files from a directory, chunks them, embeds, and stores in ChromaDB.
"""

from pathlib import Path

import chromadb
from pypdf import PdfReader

from config import get_settings
from rag.chunker import chunk_text
from rag.embeddings import EmbeddingProvider

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}


def _extract_text(file_path: Path) -> str:
    """Extract plain text from a supported file."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    # .md and .txt are plain text
    return file_path.read_text(encoding="utf-8")


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=get_settings().chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_documents(
    directory: str,
    domain: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> dict:
    """
    Ingest all supported files from a directory into the vector store.

    Args:
        directory: Path to folder containing documents.
        domain: Label for metadata filtering (e.g. "market", "tech", "shared").
        chunk_size: Override default chunk size.
        chunk_overlap: Override default chunk overlap.

    Returns:
        Summary dict with counts.
    """
    directory_path = Path(directory)
    if not directory_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    s = get_settings()
    _chunk_size = chunk_size or s.chunk_size
    _chunk_overlap = chunk_overlap or s.chunk_overlap

    embedder = EmbeddingProvider()
    chroma_client = chromadb.PersistentClient(path=s.chroma_persist_dir)
    collection = _get_collection(chroma_client)

    files_processed = 0
    total_chunks = 0

    for file_path in sorted(directory_path.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = _extract_text(file_path)
        if not text.strip():
            continue

        chunks = chunk_text(text, chunk_size=_chunk_size, chunk_overlap=_chunk_overlap)
        if not chunks:
            continue

        # Embed in batches of 100 (API limit safety)
        for batch_start in range(0, len(chunks), 100):
            batch = chunks[batch_start : batch_start + 100]
            vectors = embedder.embed(batch)

            ids = [
                f"{domain}_{file_path.stem}_{batch_start + i}"
                for i in range(len(batch))
            ]
            metadatas = [
                {
                    "domain": domain,
                    "source_file": file_path.name,
                    "chunk_index": batch_start + i,
                }
                for i in range(len(batch))
            ]

            collection.add(
                ids=ids,
                embeddings=vectors,
                documents=batch,
                metadatas=metadatas,
            )

        files_processed += 1
        total_chunks += len(chunks)

    return {
        "directory": str(directory),
        "domain": domain,
        "files_processed": files_processed,
        "total_chunks": total_chunks,
    }


def ingest_text(text: str, domain: str, source_name: str = "direct_input") -> dict:
    """Ingest a raw text string directly (useful for API-provided content)."""
    s = get_settings()
    chunks = chunk_text(text, chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
    if not chunks:
        return {"domain": domain, "total_chunks": 0}

    embedder = EmbeddingProvider()
    chroma_client = chromadb.PersistentClient(path=s.chroma_persist_dir)
    collection = _get_collection(chroma_client)

    vectors = embedder.embed(chunks)
    ids = [f"{domain}_{source_name}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"domain": domain, "source_file": source_name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)

    return {"domain": domain, "source": source_name, "total_chunks": len(chunks)}
