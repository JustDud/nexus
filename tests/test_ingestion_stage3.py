"""Stage 3 tests for crawler helpers and source constraints."""

from ingestion.crawler import extract_links, extract_text, extract_title, is_url_allowed


def test_extract_links_normalizes_http_urls():
    html = """
    <a href="/about">About</a>
    <a href="https://hugo.love/blog?tag=startup">Blog</a>
    <a href="mailto:test@example.com">Ignore</a>
    """
    links = extract_links(html, "https://hugo.love/")
    assert "https://hugo.love/about" in links
    assert "https://hugo.love/blog?tag=startup" in links
    assert all(not link.startswith("mailto:") for link in links)


def test_extract_title_and_text():
    html = "<html><head><title> Hugo Love  </title></head><body><h1>Hello</h1><p>World</p></body></html>"
    assert extract_title(html) == "Hugo Love"
    assert extract_text(html) == "Hugo Love Hello World"


def test_is_url_allowed_respects_domain_allowed_and_blocked_paths():
    allowed = ["/", "/blog", "/pricing"]
    blocked = ["/checkout", "/wp-admin"]

    assert is_url_allowed("https://hugo.love/blog/post-1", "hugo.love", allowed, blocked)
    assert not is_url_allowed("https://evil.com/blog/post-1", "hugo.love", allowed, blocked)
    assert not is_url_allowed("https://hugo.love/checkout", "hugo.love", allowed, blocked)
    assert not is_url_allowed("https://hugo.love/private", "hugo.love", allowed, blocked)
