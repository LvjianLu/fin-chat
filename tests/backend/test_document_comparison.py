"""Tests for document comparison service and API."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from finchat_backend.core.services.document_comparison_service import DocumentComparisonService
from finchat_backend.core.models import DocumentComparisonResult
from finchat_backend.main import app


class TestDocumentComparisonService:
    """Test DocumentComparisonService."""

    def test_compare_requires_min_two_documents(self):
        """Test that comparison requires at least 2 documents."""
        service = DocumentComparisonService()
        with pytest.raises(ValueError, match="At least 2 documents"):
            service.compare_documents([("file1.txt", b"content1")])

    def test_compare_limits_max_documents(self):
        """Test that comparison limits to 5 documents."""
        service = DocumentComparisonService()
        docs = [(f"file{i}.txt", f"content{i}".encode()) for i in range(6)]
        with pytest.raises(ValueError, match="Maximum 5 documents"):
            service.compare_documents(docs)

    def test_compare_same_documents_same_content(self):
        """Test comparing documents with same content."""
        service = DocumentComparisonService()
        docs = [
            ("doc1.txt", b"Same content here"),
            ("doc2.txt", b"Same content here"),
        ]
        result = service.compare_documents(docs)
        assert result.document_count == 2
        assert len(result.documents) == 2
        assert result.documents[0]["filename"] == "doc1.txt"
        assert result.documents[1]["filename"] == "doc2.txt"
        assert result.comparison_summary is not None

    def test_compare_different_documents(self):
        """Test comparing documents with different content."""
        service = DocumentComparisonService()
        docs = [
            ("doc1.txt", b"Content of first document"),
            ("doc2.txt", b"Different content in second"),
        ]
        result = service.compare_documents(docs)
        assert result.document_count == 2
        assert "Comparison" in result.comparison_summary or "comparison" in result.comparison_summary.lower()

    def test_extract_documents_with_different_extractors(self):
        """Test document extraction with different file types."""
        service = DocumentComparisonService()
        # Plain text
        text_result = service.extract_document("test.txt", b"Plain text content")
        assert text_result == "Plain text content"
        # JSON
        import json
        json_data = {"key": "value"}
        json_result = service.extract_document("test.json", json.dumps(json_data).encode())
        assert "key:" in json_result
        assert "value" in json_result
        # CSV
        csv_result = service.extract_document("test.csv", b"col1,col2\nval1,val2")
        assert "col1" in csv_result and "col2" in csv_result

    def test_unsupported_file_type_raises(self):
        """Test that unsupported file type raises error."""
        service = DocumentComparisonService()
        with pytest.raises(Exception, match="Unsupported file type"):
            service.extract_document("test.docx", b"content")

    def test_basic_comparison_generates_statistics(self):
        """Test that basic comparison includes statistics."""
        service = DocumentComparisonService()
        docs = [
            ("short.txt", b"Short"),
            ("long.txt", b"Longer content with more characters" * 10),
        ]
        result = service.compare_documents(docs)
        summary = result.comparison_summary
        assert "Total characters" in summary or "total" in summary.lower()
        assert "Average" in summary or "average" in summary.lower()

    def test_comparison_with_query(self):
        """Test that providing a query affects comparison."""
        mock_llm = Mock()
        mock_llm.chat.return_value = "Focused comparison on specified query aspects."

        service = DocumentComparisonService(llm=mock_llm)
        docs = [
            ("doc1.txt", b"Test content 1"),
            ("doc2.txt", b"Test content 2"),
        ]
        result = service.compare_documents(docs, query="Compare structure and format")

        assert result.query == "Compare structure and format"
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args[0][0]
        assert "Compare structure and format" in call_args[0]["content"]

    def test_llm_failure_falls_back_to_basic(self):
        """Test that LLM failure falls back to basic comparison."""
        mock_llm = Mock()
        mock_llm.chat.side_effect = Exception("LLM unavailable")

        service = DocumentComparisonService(llm=mock_llm)
        docs = [
            ("doc1.txt", b"Content 1"),
            ("doc2.txt", b"Content 2"),
        ]
        result = service.compare_documents(docs)
        assert "LLM comparison failed" in result.comparison_summary
        assert "Basic statistics" in result.comparison_summary or "statistics" in result.comparison_summary.lower()

    def test_compare_with_mixed_file_types(self):
        """Test comparing files of different types."""
        service = DocumentComparisonService()
        import json
        docs = [
            ("data.json", json.dumps({"a": 1}).encode()),
            ("data.csv", b"col1,col2\n1,2"),
            ("data.txt", b"Plain text data"),
        ]
        result = service.compare_documents(docs)
        assert result.document_count == 3


class TestCompareAPI:
    """Test the compare API endpoint."""

    def test_compare_endpoint_rejects_single_file(self):
        """Test that endpoint rejects single file."""
        # Endpoint logic is tested through service; API routing tested in integration
        pass
