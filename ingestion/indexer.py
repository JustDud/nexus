"""Chunk + embedding + vector indexing for cleaned crawled pages (Stage 5)."""

from dataclasses import dataclass
import json
from typing import Any

import chromadb

from config import get_settings
from rag.chunker import chunk_text
from rag.embeddings import EmbeddingProvider


@dataclass
class IndexedPageStats:
    page_id: int
    chunks_indexed: int


@dataclass
class IndexingStats:
    source_name: str
    pages_indexed: int = 0
    total_chunks: int = 0
    pages_skipped_unchanged: int = 0


def build_vector_id(source_name: str, page_id: int, chunk_index: int, content_hash: str | None) -> str:
    suffix = (content_hash or "nohash")[:12]
    return f"crawl_{source_name}_{page_id}_{chunk_index}_{suffix}"


def chunk_page_text(text: str) -> list[str]:
    s = get_settings()
    return chunk_text(text, chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)


def build_chunk_metadata(
    source_name: str,
    page: dict[str, Any],
    chunk_index: int,
) -> dict[str, Any]:
    source_metadata = page.get("source_metadata") or {}
    topic = source_metadata.get("topic")
    return {
        "domain": source_name,
        "source_file": page.get("url", "unknown"),
        "chunk_index": chunk_index,
        "source_url": page.get("url"),
        "page_id": page.get("id"),
        "title": page.get("title"),
        "topic": topic,
        "content_hash": page.get("content_hash"),
        "fetched_at": page.get("fetched_at").isoformat() if page.get("fetched_at") else None,
    }


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    s = get_settings()
    return client.get_or_create_collection(
        name=s.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def _upsert_chunks_table(cur: Any, source_id: int, page: dict[str, Any], chunks: list[str], vector_ids: list[str]) -> None:
    page_id = int(page["id"])
    # Remove stale rows if re-index changed chunk count.
    cur.execute(
        "DELETE FROM chunks WHERE page_id = %s AND chunk_index >= %s",
        (page_id, len(chunks)),
    )

    for i, text in enumerate(chunks):
        metadata = {
            "source_url": page.get("url"),
            "title": page.get("title"),
            "content_hash": page.get("content_hash"),
            "fetched_at": page.get("fetched_at").isoformat() if page.get("fetched_at") else None,
        }
        cur.execute(
            """
            INSERT INTO chunks (
                page_id, source_id, chunk_index, text, token_count,
                embedding_provider, embedding_model, vector_id, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (page_id, chunk_index)
            DO UPDATE SET
                text = EXCLUDED.text,
                token_count = EXCLUDED.token_count,
                embedding_provider = EXCLUDED.embedding_provider,
                embedding_model = EXCLUDED.embedding_model,
                vector_id = EXCLUDED.vector_id,
                metadata = EXCLUDED.metadata
            """,
            (
                page_id,
                source_id,
                i,
                text,
                len(text.split()),
                "openai",
                (
                    get_settings().embedding_model
                    if get_settings().embedding_provider.lower().strip() == "openai"
                    else get_settings().gemini_embedding_model
                ),
                vector_ids[i],
                json.dumps(metadata),
            ),
        )


def _page_already_indexed_for_hash(cur: Any, page_id: int, content_hash: str | None) -> bool:
    if not content_hash:
        return False
    cur.execute(
        """
        SELECT COUNT(*) AS total_chunks,
               COUNT(*) FILTER (WHERE metadata->>'content_hash' = %s) AS matching_hash_chunks
        FROM chunks
        WHERE page_id = %s
        """,
        (content_hash, page_id),
    )
    row = cur.fetchone()
    total_chunks = int(row["total_chunks"])
    matching = int(row["matching_hash_chunks"])
    return total_chunks > 0 and total_chunks == matching


def index_cleaned_pages(source_name: str, limit: int | None = None) -> IndexingStats:
    """
    Read cleaned pages from Postgres and index them into Chroma + chunks table.
    """
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required for ingestion indexing. "
            "Install dependencies from requirements.txt."
        ) from exc

    s = get_settings()
    stats = IndexingStats(source_name=source_name)

    embedder = EmbeddingProvider()
    chroma_client = chromadb.PersistentClient(path=s.chroma_persist_dir)
    collection = _get_collection(chroma_client)

    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM sources WHERE name = %s",
                (source_name,),
            )
            source = cur.fetchone()
            if source is None:
                raise ValueError(f"Unknown source: {source_name}")
            source_id = int(source["id"])

            query = """
                SELECT p.id, p.url, p.title, p.cleaned_text, p.content_hash, p.fetched_at
                , src.metadata AS source_metadata
                FROM pages p
                JOIN sources src ON src.id = p.source_id
                WHERE p.source_id = %s
                  AND p.cleaned_text IS NOT NULL
                  AND p.cleaned_text <> ''
                ORDER BY p.id ASC
            """
            params: tuple[Any, ...] = (source_id,)
            if limit is not None:
                query += " LIMIT %s"
                params = (source_id, limit)
            cur.execute(query, params)
            pages = cur.fetchall()

            batch_size = max(1, s.ingestion_embedding_batch_size)
            for page in pages:
                if (not s.ingestion_reindex_unchanged) and _page_already_indexed_for_hash(
                    cur,
                    page_id=int(page["id"]),
                    content_hash=page.get("content_hash"),
                ):
                    stats.pages_skipped_unchanged += 1
                    continue

                chunks = chunk_page_text(page["cleaned_text"])
                if not chunks:
                    continue

                vector_ids = [
                    build_vector_id(source_name, int(page["id"]), i, page.get("content_hash"))
                    for i in range(len(chunks))
                ]
                metadatas = [
                    build_chunk_metadata(source_name=source_name, page=page, chunk_index=i)
                    for i in range(len(chunks))
                ]

                for start in range(0, len(chunks), batch_size):
                    chunk_batch = chunks[start : start + batch_size]
                    id_batch = vector_ids[start : start + batch_size]
                    meta_batch = metadatas[start : start + batch_size]
                    vectors = embedder.embed(chunk_batch)
                    collection.upsert(
                        ids=id_batch,
                        embeddings=vectors,
                        documents=chunk_batch,
                        metadatas=meta_batch,
                    )

                _upsert_chunks_table(
                    cur,
                    source_id=source_id,
                    page=page,
                    chunks=chunks,
                    vector_ids=vector_ids,
                )

                stats.pages_indexed += 1
                stats.total_chunks += len(chunks)

            conn.commit()

    return stats
