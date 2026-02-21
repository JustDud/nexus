"""Basic web crawler for ingestion pipeline (Stage 3)."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import time
from typing import Any
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import httpx

from config import get_settings
from ingestion.extractor import process_page_for_cleaning

LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', flags=re.IGNORECASE)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", flags=re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


@dataclass
class CrawlStats:
    source_name: str
    run_id: int
    pages_discovered: int = 0
    pages_fetched: int = 0
    pages_succeeded: int = 0
    pages_failed: int = 0
    pages_unchanged: int = 0
    pages_skipped: int = 0


def extract_links(html: str, base_url: str) -> set[str]:
    links: set[str] = set()
    for raw in LINK_RE.findall(html):
        absolute = urljoin(base_url, raw.strip())
        parsed = urlparse(absolute)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
            if parsed.query:
                cleaned = f"{cleaned}?{parsed.query}"
            links.add(cleaned)
    return links


def extract_title(html: str) -> str | None:
    match = TITLE_RE.search(html)
    if not match:
        return None
    return WS_RE.sub(" ", match.group(1)).strip()


def extract_text(html: str) -> str:
    text = TAG_RE.sub(" ", html)
    return WS_RE.sub(" ", text).strip()


def is_url_allowed(
    url: str,
    source_domain: str,
    allowed_paths: list[str],
    blocked_paths: list[str],
) -> bool:
    parsed = urlparse(url)
    if parsed.netloc.lower() != source_domain.lower():
        return False

    path = parsed.path or "/"
    if blocked_paths and any(path.startswith(prefix) for prefix in blocked_paths):
        return False

    if not allowed_paths:
        return True
    for prefix in allowed_paths:
        if prefix == "/" and path == "/":
            return True
        if prefix != "/" and path.startswith(prefix):
            return True
    return False


def is_content_changed(existing_hash: str | None, new_hash: str | None) -> bool:
    if not existing_hash:
        return True
    if not new_hash:
        return True
    return existing_hash != new_hash


class BasicCrawler:
    """Crawl a source domain and persist raw pages into ingestion tables."""

    def __init__(self) -> None:
        settings = get_settings()
        self.postgres_dsn = settings.postgres_dsn
        self.user_agent = settings.ingestion_user_agent
        self.timeout_seconds = settings.ingestion_request_timeout_seconds
        self.rate_limit_seconds = settings.ingestion_rate_limit_seconds
        self.max_retries = settings.ingestion_max_retries
        self.clean_min_words = settings.ingestion_clean_min_words
        self.clean_min_unique_words = settings.ingestion_clean_min_unique_words
        self.playwright_enabled = settings.ingestion_playwright_enabled
        self.playwright_min_html_chars = settings.ingestion_playwright_min_html_chars
        self._robots_cache: dict[str, robotparser.RobotFileParser] = {}

    def _robots_for_domain(self, domain: str) -> robotparser.RobotFileParser:
        if domain in self._robots_cache:
            return self._robots_cache[domain]

        parser = robotparser.RobotFileParser()
        parser.set_url(f"https://{domain}/robots.txt")
        try:
            parser.read()
        except Exception:
            # If robots cannot be fetched, default to allow.
            parser = robotparser.RobotFileParser()
            parser.parse(["User-agent: *", "Allow: /"])
        self._robots_cache[domain] = parser
        return parser

    def _fetch_with_retries(self, client: httpx.Client, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = client.get(url, follow_redirects=True)
                return response
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2**attempt, 4))
        assert last_error is not None
        raise last_error

    def _render_with_playwright(self, url: str) -> str | None:
        if not self.playwright_enabled:
            return None
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError:
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.user_agent)
                page.goto(url, wait_until="domcontentloaded", timeout=int(self.timeout_seconds * 1000))
                html = page.content()
                browser.close()
                return html
        except Exception:
            return None

    def _should_use_playwright(self, html: str | None, source_metadata: dict[str, Any]) -> bool:
        if not self.playwright_enabled:
            return False
        if bool(source_metadata.get("render_js", False)):
            return True
        if not html:
            return True
        return len(html) < self.playwright_min_html_chars

    def _load_source(self, cur: Any, source_name: str) -> dict[str, Any]:
        cur.execute(
            """
            SELECT id, name, domain, start_urls, allowed_paths, blocked_paths, max_depth, max_pages, is_active, metadata
            FROM sources
            WHERE name = %s
            """,
            (source_name,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Unknown source: {source_name}")
        if not row["is_active"]:
            raise ValueError(f"Source is inactive: {source_name}")
        return row

    def _create_run(self, cur: Any, source_id: int) -> int:
        cur.execute(
            """
            INSERT INTO crawl_runs (source_id, status)
            VALUES (%s, 'running')
            RETURNING id
            """,
            (source_id,),
        )
        return int(cur.fetchone()["id"])

    def _finish_run(self, cur: Any, stats: CrawlStats, status: str, error_message: str | None = None) -> None:
        cur.execute(
            """
            UPDATE crawl_runs
            SET status = %s,
                finished_at = NOW(),
                pages_discovered = %s,
                pages_fetched = %s,
                pages_succeeded = %s,
                pages_failed = %s,
                pages_unchanged = %s,
                pages_skipped = %s,
                error_message = %s
            WHERE id = %s
            """,
            (
                status,
                stats.pages_discovered,
                stats.pages_fetched,
                stats.pages_succeeded,
                stats.pages_failed,
                stats.pages_unchanged,
                stats.pages_skipped,
                error_message,
                stats.run_id,
            ),
        )

    def _log_error(
        self,
        cur: Any,
        source_id: int,
        crawl_run_id: int,
        url: str | None,
        error_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        cur.execute(
            """
            INSERT INTO crawl_errors (source_id, crawl_run_id, url, error_type, message, metadata)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                source_id,
                crawl_run_id,
                url,
                error_type,
                message,
                json.dumps(metadata or {}),
            ),
        )

    def _load_existing_page(self, cur: Any, source_id: int, url: str) -> dict[str, Any] | None:
        cur.execute(
            """
            SELECT id, content_hash, metadata
            FROM pages
            WHERE source_id = %s AND url = %s
            """,
            (source_id, url),
        )
        return cur.fetchone()

    def _upsert_page(
        self,
        cur: Any,
        source_id: int,
        crawl_run_id: int,
        url: str,
        response: httpx.Response | None,
        error: str | None,
        existing_hash: str | None = None,
        rendered_html: str | None = None,
    ) -> None:
        fetched_at = datetime.now(timezone.utc)
        status_code = response.status_code if response is not None else None
        if rendered_html is not None:
            html_content = rendered_html
        else:
            html_content = response.text if response is not None and response.status_code < 400 else None
        raw_text = extract_text(html_content) if html_content else None
        cleaned = process_page_for_cleaning(
            html_content,
            min_words=self.clean_min_words,
            min_unique_words=self.clean_min_unique_words,
        ) if html_content else {"cleaned_text": "", "metrics": {"char_count": 0, "word_count": 0, "unique_word_count": 0}, "is_low_quality": True}
        content_hash = (
            hashlib.sha256(html_content.encode("utf-8")).hexdigest()
            if html_content is not None
            else None
        )
        changed = is_content_changed(existing_hash=existing_hash, new_hash=content_hash)
        title = extract_title(html_content) if html_content else None
        metadata = {"error": error} if error else {}
        metadata["quality"] = cleaned["metrics"]
        metadata["is_low_quality"] = cleaned["is_low_quality"]
        metadata["is_unchanged"] = not changed

        cur.execute(
            """
            INSERT INTO pages (
                source_id, crawl_run_id, url, canonical_url, status_code, title,
                html_content, raw_text, cleaned_text, content_hash, fetched_at, metadata, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (source_id, url)
            DO UPDATE SET
                crawl_run_id = EXCLUDED.crawl_run_id,
                canonical_url = EXCLUDED.canonical_url,
                status_code = EXCLUDED.status_code,
                title = EXCLUDED.title,
                html_content = EXCLUDED.html_content,
                raw_text = EXCLUDED.raw_text,
                cleaned_text = COALESCE(EXCLUDED.cleaned_text, pages.cleaned_text),
                content_hash = EXCLUDED.content_hash,
                fetched_at = EXCLUDED.fetched_at,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """,
            (
                source_id,
                crawl_run_id,
                url,
                url,
                status_code,
                title,
                html_content,
                raw_text,
                (
                    cleaned["cleaned_text"]
                    if (not cleaned["is_low_quality"] and changed)
                    else None
                ),
                content_hash,
                fetched_at,
                json.dumps(metadata),
            ),
        )

    def crawl_source(self, source_name: str) -> CrawlStats:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "psycopg is required for crawler persistence. "
                "Install dependencies from requirements.txt."
            ) from exc

        with psycopg.connect(self.postgres_dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                source = self._load_source(cur, source_name)
                run_id = self._create_run(cur, source_id=source["id"])
                conn.commit()

                stats = CrawlStats(source_name=source_name, run_id=run_id)
                visited: set[str] = set()
                queue: deque[tuple[str, int]] = deque((u, 0) for u in source["start_urls"])
                # Incremental recrawl: revisit previously discovered URLs for this source.
                cur.execute(
                    "SELECT url FROM pages WHERE source_id = %s ORDER BY id ASC",
                    (int(source["id"]),),
                )
                historical_urls = [row["url"] for row in cur.fetchall()]
                for old_url in historical_urls:
                    queue.append((old_url, 0))
                stats.pages_discovered = len(queue)
                source_domain = source["domain"]
                parser = self._robots_for_domain(source_domain)
                source_metadata = source.get("metadata") or {}
                ignore_robots = bool(source_metadata.get("ignore_robots", False))

                headers = {"User-Agent": self.user_agent}
                timeout = httpx.Timeout(self.timeout_seconds)

                try:
                    with httpx.Client(headers=headers, timeout=timeout) as client:
                        while queue and stats.pages_fetched < int(source["max_pages"]):
                            url, depth = queue.popleft()
                            if url in visited:
                                continue
                            visited.add(url)

                            if depth > int(source["max_depth"]):
                                stats.pages_skipped += 1
                                continue
                            if not is_url_allowed(
                                url,
                                source_domain=source_domain,
                                allowed_paths=list(source["allowed_paths"]),
                                blocked_paths=list(source["blocked_paths"]),
                            ):
                                stats.pages_skipped += 1
                                continue
                            if (not ignore_robots) and (not parser.can_fetch(self.user_agent, url)):
                                stats.pages_skipped += 1
                                self._log_error(
                                    cur,
                                    source_id=int(source["id"]),
                                    crawl_run_id=run_id,
                                    url=url,
                                    error_type="robots_disallow",
                                    message="Blocked by robots.txt",
                                    metadata={"user_agent": self.user_agent},
                                )
                                conn.commit()
                                continue

                            stats.pages_fetched += 1
                            response: httpx.Response | None = None
                            rendered_html: str | None = None
                            error_message: str | None = None
                            existing_page = self._load_existing_page(
                                cur,
                                source_id=int(source["id"]),
                                url=url,
                            )
                            existing_hash = existing_page["content_hash"] if existing_page else None
                            try:
                                response = self._fetch_with_retries(client, url)
                                if response.status_code >= 400:
                                    error_message = f"http_status_{response.status_code}"
                                    stats.pages_failed += 1
                                    self._log_error(
                                        cur,
                                        source_id=int(source["id"]),
                                        crawl_run_id=run_id,
                                        url=url,
                                        error_type="http_error",
                                        message=error_message,
                                        metadata={"status_code": response.status_code},
                                    )
                                else:
                                    stats.pages_succeeded += 1
                                    if self._should_use_playwright(response.text, source_metadata):
                                        rendered_html = self._render_with_playwright(url)
                                    new_hash = hashlib.sha256(response.text.encode("utf-8")).hexdigest()
                                    if not is_content_changed(existing_hash=existing_hash, new_hash=new_hash):
                                        stats.pages_unchanged += 1
                                    link_html = rendered_html if rendered_html is not None else response.text
                                    links = extract_links(link_html, url)
                                    for link in links:
                                        if link not in visited:
                                            queue.append((link, depth + 1))
                                            stats.pages_discovered += 1
                            except Exception as exc:
                                error_message = str(exc)
                                stats.pages_failed += 1
                                self._log_error(
                                    cur,
                                    source_id=int(source["id"]),
                                    crawl_run_id=run_id,
                                    url=url,
                                    error_type="fetch_exception",
                                    message=error_message,
                                    metadata={},
                                )

                            self._upsert_page(
                                cur,
                                source_id=int(source["id"]),
                                crawl_run_id=run_id,
                                url=url,
                                response=response,
                                error=error_message,
                                existing_hash=existing_hash,
                                rendered_html=rendered_html,
                            )
                            conn.commit()
                            if self.rate_limit_seconds > 0:
                                time.sleep(self.rate_limit_seconds)

                    self._finish_run(cur, stats=stats, status="completed", error_message=None)
                    conn.commit()
                    return stats
                except Exception as exc:
                    self._finish_run(cur, stats=stats, status="failed", error_message=str(exc))
                    conn.commit()
                    raise
