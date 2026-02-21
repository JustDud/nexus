"""Stage 4 tests for extraction, cleaning, and quality filters."""

from ingestion.extractor import (
    clean_html_to_text,
    is_low_quality_text,
    process_page_for_cleaning,
    quality_metrics,
)


def test_clean_html_to_text_removes_boilerplate_and_scripts():
    html = """
    <html>
      <head><title>Hugo</title><script>var x=1;</script></head>
      <body>
        <nav>Menu links</nav>
        <header>Top bar</header>
        <main><h1>Real Content</h1><p>Useful startup strategy details here.</p></main>
        <footer>Footer links</footer>
      </body>
    </html>
    """
    text = clean_html_to_text(html)
    assert "Real Content" in text
    assert "Useful startup strategy details here." in text
    assert "Menu links" not in text
    assert "Top bar" not in text
    assert "Footer links" not in text
    assert "var x=1;" not in text


def test_quality_metrics_counts_words_and_uniques():
    metrics = quality_metrics("alpha beta beta gamma")
    assert metrics["word_count"] == 4
    assert metrics["unique_word_count"] == 3
    assert metrics["char_count"] > 0


def test_is_low_quality_text_flags_too_short_or_low_variety():
    assert is_low_quality_text("short text", min_words=10, min_unique_words=5)
    assert is_low_quality_text("same same same same same", min_words=3, min_unique_words=3)
    assert not is_low_quality_text(
        "one two three four five six seven eight nine ten eleven",
        min_words=10,
        min_unique_words=8,
    )


def test_process_page_for_cleaning_returns_flags_and_metrics():
    result = process_page_for_cleaning(
        "<p>startup strategy product market fit growth retention monetization scale execution</p>",
        min_words=5,
        min_unique_words=5,
    )
    assert result["is_low_quality"] is False
    assert result["cleaned_text"]
    assert result["metrics"]["word_count"] >= 5
