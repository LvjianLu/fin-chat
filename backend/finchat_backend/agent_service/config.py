"""Configuration management with lightweight runtime validation."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .constants import (
    DEFAULT_DATA_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MODEL,
    OPENROUTER_BASE_URL,
)
from .models import ConfigurationError

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        """Gracefully skip .env loading when python-dotenv is unavailable."""
        return False


VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _validate_api_key(value: str) -> str:
    """Validate the OpenRouter API key."""
    if not value:
        raise ConfigurationError("API key cannot be empty")
    if not value.startswith("sk-or-"):
        raise ConfigurationError(
            "Invalid OpenRouter API key format. Keys start with 'sk-or-'"
        )
    if len(value) < 10:
        raise ConfigurationError("API key is too short")
    return value


def _validate_log_level(value: str) -> str:
    """Validate log level against the supported set."""
    normalized = (value or DEFAULT_LOG_LEVEL).upper()
    if normalized not in VALID_LOG_LEVELS:
        raise ConfigurationError(
            f"Invalid log level '{value}'. Expected one of {sorted(VALID_LOG_LEVELS)}"
        )
    return normalized


def _validate_max_document_size(value: Any) -> int:
    """Validate and normalize max document size."""
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("max_document_size must be an integer") from exc

    if size < 1_000:
        raise ConfigurationError("max_document_size must be at least 1000")
    if size > 1_000_000:
        raise ConfigurationError("max_document_size must be at most 1000000")
    return size


def _coerce_bool(value: Any) -> bool:
    """Convert environment-style values to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass
class Settings:
    """Application settings with validation."""

    openrouter_api_key: str
    openrouter_model: str = DEFAULT_MODEL
    openrouter_base_url: str = OPENROUTER_BASE_URL
    log_level: str = DEFAULT_LOG_LEVEL
    data_dir: str = DEFAULT_DATA_DIR
    max_document_size: int = 100_000
    app_name: str = "Financial Chatbot"
    debug: bool = False
    enable_tool_calling: bool = True  # Whether to enable tool calling feature

    def __post_init__(self) -> None:
        """Normalize and validate the settings payload."""
        self.openrouter_api_key = _validate_api_key(self.openrouter_api_key)
        self.log_level = _validate_log_level(self.log_level)

        # Resolve data_dir: if relative, make it relative to project root
        data_dir = self.data_dir or DEFAULT_DATA_DIR
        data_dir = os.path.expanduser(data_dir)
        if not os.path.isabs(data_dir):
            # Project root is 3 levels up from this config file:
            # config.py -> agent_service/ -> finchat_backend/ -> backend/ -> finchat/
            project_root = Path(__file__).resolve().parents[3]
            data_dir = str(project_root / data_dir)

        self.data_dir = data_dir
        self.max_document_size = _validate_max_document_size(self.max_document_size)
        self.debug = _coerce_bool(self.debug)


def _load_env_data() -> dict[str, Any]:
    """Load settings from environment variables and .env."""
    load_dotenv()
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        "openrouter_base_url": os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
        "log_level": os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        "data_dir": os.getenv("DATA_DIR", DEFAULT_DATA_DIR),
        "max_document_size": os.getenv("MAX_DOCUMENT_SIZE", 100_000),
        "app_name": os.getenv("APP_NAME", "Financial Chatbot"),
        "debug": os.getenv("DEBUG", False),
        "enable_tool_calling": os.getenv("ENABLE_TOOL_CALLING", "true").lower() in ("1", "true", "yes", "on"),
    }


def get_settings() -> Settings:
    """Get validated settings instance."""
    try:
        return Settings(**_load_env_data())
    except Exception as e:
        raise ConfigurationError(f"Configuration error: {e}") from e


def load_settings_from_dict(overrides: Optional[dict] = None) -> Settings:
    """Load settings with optional overrides (useful for testing)."""
    env_data = _load_env_data()
    if overrides:
        env_data.update(overrides)
    return Settings(**env_data)
