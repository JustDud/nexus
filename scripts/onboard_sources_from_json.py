"""Bulk onboard ingestion sources from a JSON file of links.

Input JSON format: list[object] where each object may contain:
- title, url, domain, topic, source_type, estimated_value, why_relevant, language, crawlable

Behavior:
- Normalizes URLs.
- Groups entries by (url.netloc, topic).
- Creates/updates one source per (domain, topic) with max_depth=0 so only listed URLs are crawled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ingestion.sources import CrawlSource, upsert_source


@dataclass
class LinkItem:
    title: str
    url: str
    topic: str
    source_type: str
    estimated_value: str
    why_relevant: str
    language: str
    crawlable: bool


def _normalize_url(raw: str) -> str:
    cleaned = " ".join(str(raw).split())
    return cleaned.strip()


def _slugify(value: str) -> str:
    out = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def _source_name_for(domain: str, topic: str) -> str:
    base = f"ext_{_slugify(domain)}_{_slugify(topic)}"
    if len(base) <= 55:
        return base
    suffix = hashlib.sha1(base.encode("utf-8")).hexdigest()[:8]
    return f"{base[:46]}_{suffix}"


def _load_items(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("items", "data", "sources", "results"):
            value = raw.get(key)
            if isinstance(value, list):
                return value
    raise ValueError("Unsupported JSON shape. Expected list or dict containing a list.")


def _to_link_item(obj: dict[str, Any]) -> LinkItem | None:
    url = _normalize_url(obj.get("url", ""))
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    topic = str(obj.get("topic") or "startup_strategy").strip() or "startup_strategy"
    return LinkItem(
        title=str(obj.get("title") or "Untitled").strip(),
        url=url,
        topic=topic,
        source_type=str(obj.get("source_type") or "article").strip(),
        estimated_value=str(obj.get("estimated_value") or "unknown").strip(),
        why_relevant=str(obj.get("why_relevant") or "").strip(),
        language=str(obj.get("language") or "en").strip(),
        crawlable=bool(obj.get("crawlable", True)),
    )


def onboard_from_json(path: Path, dry_run: bool = False) -> dict[str, Any]:
    items_raw = _load_items(path)

    grouped: dict[tuple[str, str], list[LinkItem]] = defaultdict(list)
    invalid = 0
    duplicates = 0
    seen_urls: set[str] = set()

    for obj in items_raw:
        if not isinstance(obj, dict):
            invalid += 1
            continue
        item = _to_link_item(obj)
        if item is None:
            invalid += 1
            continue
        if item.url in seen_urls:
            duplicates += 1
            continue
        seen_urls.add(item.url)

        domain = urlparse(item.url).netloc.lower()
        grouped[(domain, item.topic)].append(item)

    onboarded = 0
    total_urls = 0
    sources: list[str] = []

    for (domain, topic), entries in sorted(grouped.items()):
        urls = sorted({e.url for e in entries})
        paths = sorted({(urlparse(u).path or "/") for u in urls})
        source_name = _source_name_for(domain=domain, topic=topic)

        metadata: dict[str, Any] = {
            "topic": topic,
            "type": "external_curated_links",
            "imported_from": "perplexity_json",
            "items_count": len(entries),
            "crawlable_items": sum(1 for e in entries if e.crawlable),
            "source_types": sorted({e.source_type for e in entries if e.source_type}),
            "estimated_values": sorted({e.estimated_value for e in entries if e.estimated_value}),
            "languages": sorted({e.language for e in entries if e.language}),
            "titles": [e.title for e in entries[:30]],
        }

        source = CrawlSource(
            name=source_name,
            domain=domain,
            start_urls=urls,
            allowed_paths=paths,
            blocked_paths=[],
            max_depth=0,
            max_pages=max(20, len(urls) + 5),
            is_active=True,
            metadata=metadata,
        )

        if not dry_run:
            upsert_source(source)
        onboarded += 1
        total_urls += len(urls)
        sources.append(source_name)

    return {
        "items_in_file": len(items_raw),
        "invalid_items": invalid,
        "duplicate_urls": duplicates,
        "sources_created_or_updated": onboarded,
        "unique_urls": total_urls,
        "source_names": sources,
        "dry_run": dry_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard ingestion sources from JSON links.")
    parser.add_argument("json_file", type=Path, help="Path to JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Validate and summarize without DB writes")
    args = parser.parse_args()

    result = onboard_from_json(path=args.json_file, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
