"""Integration tests for external APIs."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from finchat.agent.llm.openrouter import OpenRouterClient
from finchat.integrations.sec_edgar import SECEdgarDownloader
from finchat.config import Settings, load_settings_from_dict


@pytest.mark.integration
class TestOpenRouterClient:
    """Test OpenRouter client integration."""

    def test_client_initialization(self, test_settings):
        """Test client can be initialized with valid settings."""
        # Note: This makes an actual connection test if we have a real API key
        # In CI, we'd use a mock API or skip
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-test1234567890",
            }
        )
        client = OpenRouterClient(settings)
        assert client.is_available()
        assert client.model == settings.openrouter_model

    def test_client_rejects_invalid_key(self):
        """Test that client initialization fails with invalid key."""
        with pytest.raises(Exception):  # ConfigurationError or connection error
            settings = load_settings_from_dict(
                {
                    "openrouter_api_key": "invalid-key",
                }
            )
            OpenRouterClient(settings)

    def test_build_messages(self, test_settings):
        """Test message building."""
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-test1234567890",
            }
        )
        client = OpenRouterClient(settings)

        messages = client.build_messages(
            system_prompt="You are a helpful assistant",
            user_message="Hello",
            document_context=None,
            conversation_history=[],
        )

        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_build_messages_with_document(self, test_settings):
        """Test message building with document context."""
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-test1234567890",
            }
        )
        client = OpenRouterClient(settings)

        messages = client.build_messages(
            system_prompt="System prompt",
            user_message="Question",
            document_context="Document text here",
            conversation_history=[],
        )

        # Should have: system, document system, user
        assert len(messages) == 3
        assert any("Document Context" in m["content"] for m in messages)

    def test_build_messages_with_history(self, test_settings):
        """Test message building with conversation history."""
        from finchat.models import ChatMessage

        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-test1234567890",
            }
        )
        client = OpenRouterClient(settings)

        history = [
            ChatMessage(role="user", content="Question 1"),
            ChatMessage(role="assistant", content="Answer 1"),
        ]

        messages = client.build_messages(
            system_prompt="System prompt",
            user_message="Question 2",
            conversation_history=history,
        )

        # system + 2 history + current user = 4 messages
        assert len(messages) == 4


class TestSECEdgarDownloader:
    """Test SEC EDGAR downloader integration."""

    def test_downloader_initialization(self):
        """Test downloader can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = SECEdgarDownloader(email="test@example.com", data_dir=tmpdir)
            assert downloader.data_dir == Path(tmpdir).resolve()

    def test_download_filing_invalid_ticker(self):
        """Test download with invalid ticker raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = SECEdgarDownloader(data_dir=tmpdir)
            with pytest.raises(Exception):  # SECDownloadError
                downloader.download_filing("INVALIDTICKER", "10-K")

    def test_download_filing_invalid_type(self):
        """Test download with invalid filing type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = SECEdgarDownloader(data_dir=tmpdir)
            with pytest.raises(Exception, match="Unsupported filing type"):
                downloader.download_filing("AAPL", "99-K")

    def test_read_filing_missing_file(self):
        """Test reading non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = SECEdgarDownloader(data_dir=tmpdir)
            non_existent = Path(tmpdir) / "nonexistent.txt"
            with pytest.raises(Exception):  # SECDownloadError
                downloader.read_filing(non_existent)

    def test_extract_sections_from_sample_text(self):
        """Test section extraction from sample filing text."""
        downloader = SECEdgarDownloader()

        sample_text = """
        ITEM 1. BUSINESS

        Our company is a technology leader...
        We have various products and services.

        ITEM 1A. RISK FACTORS

        There are many risks including market competition.
        """
        sections = downloader.extract_financial_sections(sample_text)

        assert "business_overview" in sections
        assert "risk_factors" in sections
        assert "Our company" in sections["business_overview"]


