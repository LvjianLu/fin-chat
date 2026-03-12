"""Tests for configuration module."""

import pytest

from agent_service.config import Settings, load_settings_from_dict
from agent_service.models import ConfigurationError


class TestSettings:
    """Test Settings model."""

    def test_valid_settings(self):
        """Test that valid settings load correctly."""
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-valid1234567890",
                "openrouter_model": "anthropic/claude-3.7-sonnet",
                "log_level": "DEBUG",
                "data_dir": "/tmp/test_data",
            }
        )
        assert settings.openrouter_api_key == "sk-or-valid1234567890"
        assert settings.openrouter_model == "anthropic/claude-3.7-sonnet"
        assert settings.log_level == "DEBUG"
        assert settings.data_dir == "/tmp/test_data"

    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(ConfigurationError):
            load_settings_from_dict({"openrouter_api_key": ""})

    def test_invalid_api_key_format(self):
        """Test that invalid API key format raises error."""
        with pytest.raises(ConfigurationError):
            load_settings_from_dict({"openrouter_api_key": "invalid-key"})

    def test_api_key_too_short(self):
        """Test that too-short API key raises error."""
        with pytest.raises(ConfigurationError):
            load_settings_from_dict({"openrouter_api_key": "sk-or-123"})

    def test_invalid_log_level(self):
        """Test that invalid log level raises error."""
        with pytest.raises(ConfigurationError):
            load_settings_from_dict(
                {
                    "openrouter_api_key": "sk-or-valid1234567890",
                    "log_level": "INVALID",
                }
            )

    def test_valid_log_levels(self):
        """Test all valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = load_settings_from_dict(
                {
                    "openrouter_api_key": "sk-or-valid1234567890",
                    "log_level": level,
                }
            )
            assert settings.log_level == level

    def test_default_values(self):
        """Test that default values are applied."""
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-valid1234567890",
            }
        )
        assert settings.openrouter_model == "stepfun/step-3.5-flash:free"
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
        assert settings.max_document_size == 100_000

    def test_max_document_size_validation(self):
        """Test max document size validation."""
        # Valid range
        settings = load_settings_from_dict(
            {
                "openrouter_api_key": "sk-or-valid1234567890",
                "max_document_size": 50000,
            }
        )
        assert settings.max_document_size == 50000

        # Too small
        with pytest.raises(ConfigurationError):
            load_settings_from_dict(
                {
                    "openrouter_api_key": "sk-or-valid1234567890",
                    "max_document_size": 100,
                }
            )

        # Too large
        with pytest.raises(ConfigurationError):
            load_settings_from_dict(
                {
                    "openrouter_api_key": "sk-or-valid1234567890",
                    "max_document_size": 2_000_000,
                }
            )
