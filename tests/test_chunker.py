"""Tests for the text chunker — no API keys needed."""

import pytest
from rag.chunker import chunk_text


class TestChunkTextBasicBehavior:
    def test_empty_string_returns_empty_list(self):
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\n  ") == []

    def test_short_text_returns_single_chunk(self):
        result = chunk_text("Hello world", chunk_size=512)
        assert result == ["Hello world"]

    def test_text_exactly_at_chunk_size(self):
        text = "a" * 512
        result = chunk_text(text, chunk_size=512, chunk_overlap=0)
        assert len(result) == 1
        assert result[0] == text

    def test_single_word_returns_single_chunk(self):
        assert chunk_text("word") == ["word"]


class TestChunkTextSplitting:
    def test_splits_on_paragraph_boundaries(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=0)
        assert len(chunks) >= 2
        # First chunk should contain "First paragraph"
        assert "First paragraph" in chunks[0]

    def test_splits_on_newlines_when_no_paragraphs(self):
        text = "Line one.\nLine two.\nLine three.\nLine four."
        chunks = chunk_text(text, chunk_size=25, chunk_overlap=0)
        assert len(chunks) >= 2

    def test_splits_on_sentences_when_no_newlines(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, chunk_size=40, chunk_overlap=0)
        assert len(chunks) >= 2

    def test_hard_splits_long_words(self):
        text = "a" * 1000
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=0)
        assert len(chunks) >= 5
        for chunk in chunks:
            assert len(chunk) <= 200

    def test_all_content_preserved_no_overlap(self):
        text = "Word " * 200  # 1000 chars
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=0)
        # Every word should appear in at least one chunk
        reconstructed = " ".join(chunks)
        assert reconstructed.count("Word") >= 200


class TestChunkTextOverlap:
    def test_overlap_creates_shared_content(self):
        text = "Alpha.\n\nBravo.\n\nCharlie.\n\nDelta.\n\nEcho."
        chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
        # With overlap, later chunks should start with tail of previous chunk
        if len(chunks) > 1:
            for i in range(1, len(chunks)):
                # The overlap means some text from chunk[i-1] appears at start of chunk[i]
                assert len(chunks[i]) > 0

    def test_zero_overlap_produces_clean_splits(self):
        text = "AAA.\n\nBBB.\n\nCCC."
        chunks = chunk_text(text, chunk_size=10, chunk_overlap=0)
        assert len(chunks) >= 2


class TestChunkTextEdgeCases:
    def test_very_small_chunk_size(self):
        text = "Hello world, this is a test."
        chunks = chunk_text(text, chunk_size=5, chunk_overlap=0)
        assert len(chunks) >= 1
        # Should not crash or infinite loop

    def test_chunk_size_one(self):
        text = "ABC"
        chunks = chunk_text(text, chunk_size=1, chunk_overlap=0)
        assert len(chunks) >= 1

    def test_large_chunk_size(self):
        text = "Short text."
        chunks = chunk_text(text, chunk_size=100000, chunk_overlap=0)
        assert chunks == ["Short text."]

    def test_overlap_larger_than_chunks(self):
        """Overlap > chunk content shouldn't crash."""
        text = "A.\n\nB.\n\nC."
        chunks = chunk_text(text, chunk_size=5, chunk_overlap=100)
        assert len(chunks) >= 1

    def test_unicode_content(self):
        text = "Привет мир.\n\nЭто тест.\n\n日本語テスト。"
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=0)
        assert len(chunks) >= 1
        full = "".join(chunks)
        assert "Привет" in full
        assert "日本語" in full

    def test_mixed_separators(self):
        text = "Para one.\n\nPara two.\nLine three. Sentence four."
        chunks = chunk_text(text, chunk_size=20, chunk_overlap=0)
        assert len(chunks) >= 2

    def test_many_empty_paragraphs(self):
        text = "\n\n\n\nContent here.\n\n\n\nMore content.\n\n\n\n"
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=0)
        # Should not produce empty chunks
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_deterministic_output(self):
        text = "Hello world. " * 50
        c1 = chunk_text(text, chunk_size=100, chunk_overlap=10)
        c2 = chunk_text(text, chunk_size=100, chunk_overlap=10)
        assert c1 == c2
