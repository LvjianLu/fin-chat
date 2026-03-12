"""Tests for utility modules."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from agent_service.utils.validators import (
    validate_ticker,
    validate_file_upload,
    validate_api_key,
    validate_filing_type,
    validate_email,
    validate_positive_int,
)
from agent_service.utils.text_utils import (
    truncate_text,
    clean_text,
    sanitize_filename,
    extract_numbers_with_context,
)
from agent_service.utils.file_utils import (
    ensure_data_directory,
    read_file_safe,
    is_safe_filepath,
)


class TestValidateTicker:
    """Test ticker validation."""

    def test_valid_tickers(self):
        """Test valid ticker symbols."""
        assert validate_ticker("aapl") == "AAPL"
        assert validate_ticker("MSFT") == "MSFT"
        assert validate_ticker("googl") == "GOOGL"
        assert validate_ticker("A") == "A"
        assert validate_ticker("aaaaa") == "AAAAA"

    def test_invalid_tickers(self):
        """Test invalid ticker symbols."""
        invalid = ["", "123", "ABCDEF", "aa-aa", "a b", "aa b"]
        for ticker in invalid:
            with pytest.raises(ValueError, match="Invalid ticker"):
                validate_ticker(ticker)


class TestValidateAPIKey:
    """Test API key validation."""

    def test_valid_key(self):
        """Test valid OpenRouter API key."""
        key = "sk-or-1234567890abcdef"
        assert validate_api_key(key) == key

    def test_key_must_start_with_prefix(self):
        """Test that key must start with sk-or-."""
        with pytest.raises(ValueError, match="Invalid OpenRouter API key format"):
            validate_api_key("sk-test1234567890")

    def test_key_cannot_be_empty(self):
        """Test that empty key is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_api_key("")

    def test_key_too_short(self):
        """Test that too-short key is rejected."""
        with pytest.raises(ValueError, match="too short"):
            validate_api_key("sk-or-123")


class TestValidateFileUpload:
    """Test file upload validation."""

    def test_valid_file(self):
        """Test valid file upload."""
        mock_file = Mock()
        mock_file.name = "document.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        assert validate_file_upload(mock_file) is True

    def test_unsupported_extension(self):
        """Test unsupported file type."""
        mock_file = Mock()
        mock_file.name = "document.docx"
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_upload(mock_file)

    def test_file_too_large(self):
        """Test file exceeding size limit."""
        from agent_service.constants import MAX_UPLOAD_SIZE_BYTES

        mock_file = Mock()
        mock_file.name = "large.pdf"
        mock_file.size = MAX_UPLOAD_SIZE_BYTES + 1

        with pytest.raises(ValueError, match="File too large"):
            validate_file_upload(mock_file)

    def test_multiple_supported_extensions(self):
        """Test different supported file types."""
        for ext in ["txt", "pdf", "htm", "html"]:
            mock_file = Mock()
            mock_file.name = f"document.{ext}"
            assert validate_file_upload(mock_file) is True


class TestValidateFilingType:
    """Test SEC filing type validation."""

    def test_valid_filing_types(self):
        """Test valid filing types."""
        assert validate_filing_type("10-K") == "10-K"
        assert validate_filing_type("10-Q") == "10-Q"
        assert validate_filing_type("8-K") == "8-K"
        assert validate_filing_type("10-k") == "10-K"
        assert validate_filing_type("10-q") == "10-Q"

    def test_invalid_filing_type(self):
        """Test invalid filing type."""
        with pytest.raises(ValueError, match="Unsupported filing type"):
            validate_filing_type("20-F")

    def test_empty_filing_type(self):
        """Test empty filing type."""
        with pytest.raises(ValueError):
            validate_filing_type("")


class TestValidateEmail:
    """Test email validation."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        valid = ["user@example.com", "test.user@domain.co.uk", "a@b.co"]
        for email in valid:
            validate_email(email)

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        invalid = ["", "not-an-email", "missing@domain", "@domain.com", "user@.com"]
        for email in invalid:
            with pytest.raises(ValueError, match="Invalid email"):
                validate_email(email)


class TestValidatePositiveInt:
    """Test positive integer validation."""

    def test_valid_values(self):
        """Test valid positive integers."""
        assert validate_positive_int(1) == 1
        assert validate_positive_int(50) == 50
        assert validate_positive_int(100) == 100

    def test_invalid_type(self):
        """Test non-integer types."""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_positive_int(5.5)
        with pytest.raises(ValueError, match="must be an integer"):
            validate_positive_int("10")

    def test_out_of_range(self):
        """Test values outside allowed range."""
        with pytest.raises(ValueError, match="must be between"):
            validate_positive_int(0, min_val=1)
        with pytest.raises(ValueError, match="must be between"):
            validate_positive_int(101, max_val=100)


class TestTruncateText:
    """Test text truncation."""

    def test_no_truncation_needed(self):
        """Test short text remains unchanged."""
        text = "Short text"
        assert truncate_text(text, 100) == text

    def test_basic_truncation(self):
        """Test basic truncation."""
        text = "x" * 200
        result = truncate_text(text, 100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_truncate_keep_end(self):
        """Test truncation keeping end of text."""
        text = "A" * 50 + "B" * 50
        result = truncate_text(text, 60, keep_end=True)
        assert result.startswith("...")
        assert result.endswith("B" * 50)

    def test_exact_length(self):
        """Test text exactly at limit."""
        text = "x" * 100
        assert truncate_text(text, 100) == text


class TestCleanText:
    """Test text cleaning."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "  Multiple    spaces   and\n\nnewlines  "
        result = clean_text(text)
        assert result == "Multiple spaces and newlines"

    def test_empty_text(self):
        """Test empty text."""
        assert clean_text("") == ""
        assert clean_text("   ") == ""

    def test_single_line(self):
        """Test single line text."""
        assert clean_text("Hello world") == "Hello world"


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_remove_path(self):
        """Test that path components are removed."""
        assert sanitize_filename("/path/to/file.txt") == "file.txt"
        assert sanitize_filename("C:\\folder\\file.txt") == "file.txt"

    def test_replace_invalid_chars(self):
        """Test that invalid characters are replaced."""
        assert sanitize_filename("file<test>.txt") == "file_test_.txt"

    def test_truncate_long_name(self):
        """Test that long names are truncated."""
        long_name = "a" * 150 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_normal_name(self):
        """Test normal filename."""
        assert sanitize_filename("my_document.txt") == "my_document.txt"


class TestExtractNumbersWithContext:
    """Test number extraction."""

    def test_extract_dollar_amounts(self):
        """Test extraction of dollar amounts."""
        text = "Revenue was $100 million and costs were $50.5 million."
        results = extract_numbers_with_context(text)
        assert len(results) > 0
        dollar_results = [r for r in results if r["match"].startswith("$")]
        assert len(dollar_results) >= 2

    def test_extract_with_query_filter(self):
        """Test extraction filtered by query."""
        text = "Revenue is $100 million. Net income is $50 million."
        results = extract_numbers_with_context(text, query="revenue")
        assert len(results) > 0
        for r in results:
            assert "revenue" in r["context"].lower()

    def test_no_matches(self):
        """Test text with no matches."""
        text = "There are no numbers here, just plain text."
        results = extract_numbers_with_context(text)
        assert len(results) == 0

    def test_context_includes_surrounding_text(self):
        """Test that context includes surrounding text."""
        text = "x" * 100 + " $123 " + "y" * 100  # Put $123 in middle
        results = extract_numbers_with_context(text, context_chars=10)
        assert len(results) > 0
        context = results[0]["context"]
        # Context should include some of the x's and y's
        assert "x" in context or "$123" in context
