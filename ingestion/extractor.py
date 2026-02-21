"""HTML cleaning and quality filtering for ingestion pipeline (Stage 4)."""

import re
from typing import Any

SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript)[^>]*>.*?</\1>",
    flags=re.IGNORECASE | re.DOTALL,
)
BOILERPLATE_BLOCK_RE = re.compile(
    r"<(nav|header|footer|aside|form)[^>]*>.*?</\1>",
    flags=re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SPLIT_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_-]*")


def clean_html_to_text(html: str | None) -> str:
    if not html:
        return ""
    text = SCRIPT_STYLE_RE.sub(" ", html)
    text = BOILERPLATE_BLOCK_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    text = WS_RE.sub(" ", text).strip()
    return text


def quality_metrics(text: str) -> dict[str, int]:
    words = SPLIT_WORD_RE.findall(text)
    unique_words = len(set(w.lower() for w in words))
    return {
        "char_count": len(text),
        "word_count": len(words),
        "unique_word_count": unique_words,
    }


def is_low_quality_text(text: str, min_words: int, min_unique_words: int) -> bool:
    metrics = quality_metrics(text)
    if metrics["word_count"] < min_words:
        return True
    if metrics["unique_word_count"] < min_unique_words:
        return True
    return False


def process_page_for_cleaning(
    html_content: str | None,
    min_words: int,
    min_unique_words: int,
) -> dict[str, Any]:
    cleaned = clean_html_to_text(html_content)
    metrics = quality_metrics(cleaned)
    return {
        "cleaned_text": cleaned,
        "metrics": metrics,
        "is_low_quality": is_low_quality_text(
            cleaned,
            min_words=min_words,
            min_unique_words=min_unique_words,
        ),
    }
