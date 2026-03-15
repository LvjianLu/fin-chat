"""Tests for document extractors."""

import pytest

from finchat_backend.core.extractors.base import TextExtractor
from finchat_backend.core.extractors.text import PlainTextExtractor
from finchat_backend.core.extractors.pdf import PdfTextExtractor
from finchat_backend.core.extractors.html import HtmlTextExtractor
from finchat_backend.core.extractors.json import JsonTextExtractor
from finchat_backend.core.extractors.csv import CsvTextExtractor


class TestTextExtractorInterface:
    """Test the TextExtractor interface."""

    def test_all_extractors_implement_can_handle(self):
        """Test all extractors implement can_handle method."""
        extractors: list[TextExtractor] = [
            PlainTextExtractor(),
            PdfTextExtractor(),
            HtmlTextExtractor(),
            JsonTextExtractor(),
            CsvTextExtractor(),
        ]
        for extractor in extractors:
            assert hasattr(extractor, "can_handle")
            assert callable(extractor.can_handle)

    def test_all_extractors_implement_extract(self):
        """Test all extractors implement extract method."""
        extractors: list[TextExtractor] = [
            PlainTextExtractor(),
            PdfTextExtractor(),
            HtmlTextExtractor(),
            JsonTextExtractor(),
            CsvTextExtractor(),
        ]
        for extractor in extractors:
            assert hasattr(extractor, "extract")
            assert callable(extractor.extract)

    def test_all_extractors_have_extensions(self):
        """Test all extractors define extensions."""
        extractors: list[TextExtractor] = [
            PlainTextExtractor(),
            PdfTextExtractor(),
            HtmlTextExtractor(),
            JsonTextExtractor(),
            CsvTextExtractor(),
        ]
        for extractor in extractors:
            assert hasattr(extractor, "extensions")
            assert isinstance(extractor.extensions, tuple)
            assert len(extractor.extensions) > 0


class TestPlainTextExtractor:
    """Test PlainTextExtractor."""

    def test_can_handle_txt_files(self):
        """Test can_handle identifies .txt files."""
        extractor = PlainTextExtractor()
        assert extractor.can_handle("document.txt")
        assert extractor.can_handle("file.TXT")
        assert not extractor.can_handle("document.pdf")

    def test_extracts_utf8_text(self):
        """Test extraction of UTF-8 text."""
        extractor = PlainTextExtractor()
        content = "Hello, World! 你好世界".encode("utf-8")
        result = extractor.extract(content)
        assert result == "Hello, World! 你好世界"


class TestPdfTextExtractor:
    """Test PdfTextExtractor."""

    def test_can_handle_pdf_files(self):
        """Test can_handle identifies .pdf files."""
        extractor = PdfTextExtractor()
        assert extractor.can_handle("document.pdf")
        assert extractor.can_handle("file.PDF")
        assert not extractor.can_handle("document.txt")

    def test_extracts_text_from_simple_pdf(self):
        """Test extraction from a simple PDF."""
        # This test requires a sample PDF file
        # For now, we'll create a minimal PDF with pypdf
        import io
        try:
            from pypdf import PdfWriter, PdfReader
        except ImportError:
            from PyPDF2 import PdfWriter, PdfReader

        extractor = PdfTextExtractor()

        # Create a simple PDF in memory with some text
        packet = io.BytesIO()
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        output = io.BytesIO()
        writer.write(output)
        pdf_bytes = output.getvalue()

        # Should not raise error even if extraction returns empty
        result = extractor.extract(pdf_bytes)
        assert isinstance(result, str)


class TestHtmlTextExtractor:
    """Test HtmlTextExtractor."""

    def test_can_handle_html_files(self):
        """Test can_handle identifies .html and .htm files."""
        extractor = HtmlTextExtractor()
        assert extractor.can_handle("document.html")
        assert extractor.can_handle("file.htm")
        assert extractor.can_handle("page.HTML")
        assert not extractor.can_handle("document.txt")

    def test_extracts_readable_text(self):
        """Test extraction of readable text from HTML."""
        extractor = HtmlTextExtractor()
        html = b"<html><body><h1>Title</h1><p>Hello <b>World</b>!</p></body></html>"
        result = extractor.extract(html)
        assert "Title" in result
        assert "Hello" in result
        assert "World" in result

    def test_collapses_whitespace(self):
        """Test that whitespace is normalized."""
        extractor = HtmlTextExtractor()
        html = b"<div>Multiple    spaces   and\n\nnewlines</div>"
        result = extractor.extract(html)
        # Should have normalized whitespace
        assert "  " not in result or len(result.strip().split()) <= 3
        assert "Multiple" in result
        assert "spaces" in result


class TestJsonTextExtractor:
    """Test JsonTextExtractor."""

    def test_can_handle_json_files(self):
        """Test can_handle identifies .json files."""
        extractor = JsonTextExtractor()
        assert extractor.can_handle("data.json")
        assert extractor.can_handle("config.JSON")
        assert not extractor.can_handle("data.txt")

    def test_extracts_simple_json(self):
        """Test extraction from simple JSON object."""
        extractor = JsonTextExtractor()
        json_data = {"name": "test", "value": 123}
        import json
        content = json.dumps(json_data).encode("utf-8")
        result = extractor.extract(content)
        assert "name:" in result
        assert "test" in result
        assert "value:" in result
        assert "123" in result

    def test_extracts_nested_json(self):
        """Test extraction from nested JSON."""
        extractor = JsonTextExtractor()
        json_data = {
            "company": "ACME",
            "financials": {
                "revenue": 1000000,
                "expenses": 500000,
            },
            "departments": [
                {"name": "Sales", "employees": 10},
                {"name": "Engineering", "employees": 20},
            ],
        }
        import json
        content = json.dumps(json_data).encode("utf-8")
        result = extractor.extract(content)
        assert "company:" in result
        assert "ACME" in result
        assert "revenue:" in result
        assert "Sales" in result
        assert "Engineering" in result

    def test_extracts_json_array(self):
        """Test extraction from JSON array."""
        extractor = JsonTextExtractor()
        json_data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        import json
        content = json.dumps(json_data).encode("utf-8")
        result = extractor.extract(content)
        assert "Item 1" in result
        assert "Item 2" in result

    def test_handles_invalid_json(self):
        """Test that invalid JSON raises error."""
        extractor = JsonTextExtractor()
        content = b"{ invalid json }"
        with pytest.raises(ValueError, match="Invalid JSON file"):
            extractor.extract(content)


class TestCsvTextExtractor:
    """Test CsvTextExtractor."""

    def test_can_handle_csv_files(self):
        """Test can_handle identifies .csv files."""
        extractor = CsvTextExtractor()
        assert extractor.can_handle("data.csv")
        assert extractor.can_handle("file.CSV")
        assert not extractor.can_handle("data.txt")

    def test_extracts_simple_csv(self):
        """Test extraction from simple CSV."""
        extractor = CsvTextExtractor()
        csv_data = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
        result = extractor.extract(csv_data)
        assert "name | age | city" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result

    def test_extracts_csv_without_header(self):
        """Test extraction from CSV without header."""
        extractor = CsvTextExtractor()
        csv_data = b"value1,value2,value3\nval1,val2,val3"
        result = extractor.extract(csv_data)
        assert "value1" in result and "value2" in result

    def test_handles_quoted_values(self):
        """Test extraction with quoted values containing commas."""
        extractor = CsvTextExtractor()
        csv_data = b'"Name","Description"\n"John Doe","Developer, Manager"'
        result = extractor.extract(csv_data)
        assert "John Doe" in result
        assert "Developer, Manager" in result

    def test_handles_empty_csv(self):
        """Test extraction from empty CSV."""
        extractor = CsvTextExtractor()
        result = extractor.extract(b"")
        assert result == ""
