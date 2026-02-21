"""Manual import lane for local PDFs/Markdown/TXT files."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from config import get_settings
from ingestion.extractor import process_page_for_cleaning
from ingestion.indexer import index_cleaned_pages
from ingestion.sources import CrawlSource, upsert_source

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


@dataclass
class ManualImportStats:
    source_name: str
    files_seen: int = 0
    files_imported: int = 0
    files_low_quality: int = 0
    pages_indexed: int = 0
    total_chunks: int = 0


def _read_file_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _ensure_manual_source(source_name: str, topic: str) -> None:
    source = CrawlSource(
        name=source_name,
        domain="local.manual",
        start_urls=["file://local-import"],
        allowed_paths=["/"],
        blocked_paths=[],
        max_depth=0,
        max_pages=100000,
        is_active=False,
        metadata={"topic": topic, "type": "manual_import"},
    )
    upsert_source(source)


def import_directory(
    directory: str,
    source_name: str = "startup_strategy_pack",
    topic: str = "startup_strategy",
    recursive: bool = True,
    index_after_import: bool = True,
) -> dict[str, Any]:
    """
    Import local docs into pages table and optionally index them into Chroma.
    """
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for manual import.") from exc

    s = get_settings()
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    _ensure_manual_source(source_name=source_name, topic=topic)
    stats = ManualImportStats(source_name=source_name)

    with psycopg.connect(s.postgres_dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(f"Source not found after upsert: {source_name}")
            source_id = int(row["id"])

            file_iter = root.rglob("*") if recursive else root.iterdir()
            for file_path in sorted(file_iter):
                if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                stats.files_seen += 1

                text = _read_file_text(file_path)
                cleaned = process_page_for_cleaning(
                    html_content=text,
                    min_words=s.ingestion_clean_min_words,
                    min_unique_words=s.ingestion_clean_min_unique_words,
                )
                if cleaned["is_low_quality"]:
                    stats.files_low_quality += 1

                url = f"file://{file_path.resolve()}"
                metadata = {
                    "quality": cleaned["metrics"],
                    "is_low_quality": cleaned["is_low_quality"],
                    "manual_import": True,
                    "topic": topic,
                }
                cur.execute(
                    """
                    INSERT INTO pages (
                        source_id, crawl_run_id, url, canonical_url, status_code, title,
                        html_content, raw_text, cleaned_text, content_hash, fetched_at, metadata, updated_at
                    )
                    VALUES (%s, NULL, %s, %s, 200, %s, %s, %s, %s, md5(%s), NOW(), %s::jsonb, NOW())
                    ON CONFLICT (source_id, url)
                    DO UPDATE SET
                        status_code = EXCLUDED.status_code,
                        title = EXCLUDED.title,
                        html_content = EXCLUDED.html_content,
                        raw_text = EXCLUDED.raw_text,
                        cleaned_text = EXCLUDED.cleaned_text,
                        content_hash = EXCLUDED.content_hash,
                        fetched_at = EXCLUDED.fetched_at,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    (
                        source_id,
                        url,
                        url,
                        file_path.name,
                        text,
                        text,
                        None if cleaned["is_low_quality"] else cleaned["cleaned_text"],
                        text,
                        json.dumps(metadata),
                    ),
                )
                stats.files_imported += 1

            conn.commit()

    if index_after_import:
        indexed = index_cleaned_pages(source_name=source_name)
        stats.pages_indexed = indexed.pages_indexed
        stats.total_chunks = indexed.total_chunks

    return {
        "source_name": stats.source_name,
        "files_seen": stats.files_seen,
        "files_imported": stats.files_imported,
        "files_low_quality": stats.files_low_quality,
        "pages_indexed": stats.pages_indexed,
        "total_chunks": stats.total_chunks,
    }
