"""Tests for the ingestion pipeline — tests file extraction and chunking without API calls."""

# conftest.py sets dummy API keys before this module loads.

from pathlib import Path

import pytest

from rag.ingest import _extract_text, SUPPORTED_EXTENSIONS


class TestSupportedExtensions:
    def test_pdf_supported(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_markdown_supported(self):
        assert ".md" in SUPPORTED_EXTENSIONS

    def test_text_supported(self):
        assert ".txt" in SUPPORTED_EXTENSIONS

    def test_unsupported_excluded(self):
        assert ".docx" not in SUPPORTED_EXTENSIONS
        assert ".csv" not in SUPPORTED_EXTENSIONS
        assert ".json" not in SUPPORTED_EXTENSIONS


class TestExtractText:
    def test_extract_from_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello from a text file.", encoding="utf-8")
        result = _extract_text(f)
        assert result == "Hello from a text file."

    def test_extract_from_md(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Heading\n\nParagraph content.", encoding="utf-8")
        result = _extract_text(f)
        assert "# Heading" in result
        assert "Paragraph content." in result

    def test_extract_from_txt_unicode(self, tmp_path):
        f = tmp_path / "unicode.txt"
        f.write_text("Привет мир 🌍 日本語", encoding="utf-8")
        result = _extract_text(f)
        assert "Привет" in result
        assert "日本語" in result

    def test_extract_from_empty_txt(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = _extract_text(f)
        assert result == ""

    def test_extract_from_multiline_txt(self, tmp_path):
        content = "Line 1\nLine 2\n\nParagraph 2"
        f = tmp_path / "multi.txt"
        f.write_text(content, encoding="utf-8")
        result = _extract_text(f)
        assert result == content


class TestIngestDocumentsValidation:
    def test_nonexistent_directory_raises(self):
        from rag.ingest import ingest_documents
        with pytest.raises(FileNotFoundError):
            ingest_documents("/nonexistent/path", domain="test")

    def test_file_path_instead_of_dir_raises(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("content")
        from rag.ingest import ingest_documents
        with pytest.raises(FileNotFoundError):
            ingest_documents(str(f), domain="test")
