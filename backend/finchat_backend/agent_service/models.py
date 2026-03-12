"""Custom exceptions and data models for the financial chatbot."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class FinChatError(Exception):
    """Base exception for all chatbot-related errors."""

    pass


class ConfigurationError(FinChatError, ValueError):
    """Raised when configuration is invalid or missing."""

    pass


class DocumentError(FinChatError):
    """Raised when document operations fail."""

    pass


class APIError(FinChatError):
    """Raised when external API calls fail."""

    pass


class ValidationError(FinChatError, ValueError):
    """Raised when input validation fails."""

    pass


class SECDownloadError(FinChatError):
    """Raised when SEC filing download fails."""

    pass


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    role: str  # "user" or "assistant"
    content: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API."""
        return {"role": self.role, "content": self.content}


@dataclass
class DocumentMetadata:
    """Metadata for loaded documents."""

    source_name: str
    character_count: int
    is_loaded: bool = True

    @property
    def size_summary(self) -> str:
        """Get human-readable size summary."""
        return f"{self.character_count:,} characters"


@dataclass
class SearchResult:
    """Result from document search."""

    query: str
    matches: List[Dict[str, Any]]
    total_matches: int
    displayed_matches: int

    def format_results(self, limit: int = 5) -> str:
        """Format search results for display."""
        if not self.matches:
            return f"No matches found for '{self.query}'."

        result_text = f"Found {self.total_matches} matches for '{self.query}':\n\n"
        for i, match in enumerate(self.matches[:limit], 1):
            result_text += f"{i}. {match.get('match', 'N/A')}\n"
            context = match.get("context", "")
            if context:
                result_text += f"   Context: ...{context}...\n\n"

        if self.total_matches > limit:
            result_text += f"\n... and {self.total_matches - limit} more matches."

        return result_text


@dataclass
class FinMetric:
    """Extracted financial metric with context."""

    name: str
    value: str
    context: str
    source_section: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


# Type aliases for clarity
MessageList = List[Dict[str, str]]
ConversationHistory = List[ChatMessage]
