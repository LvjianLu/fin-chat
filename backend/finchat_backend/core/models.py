"""Backend DTOs for sessions and document operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


MessagePayload = dict[str, Any]


@dataclass
class SessionRecord:
    """Serializable session state."""

    id: str
    title: str
    messages: list[MessagePayload] = field(default_factory=list)
    doc_source: Optional[str] = None
    document_content: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    saved_at: Optional[datetime] = None

    @property
    def message_count(self) -> int:
        """Return the number of messages in the record."""
        return len(self.messages)

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to the persisted JSON shape."""
        return {
            "id": self.id,
            "title": self.title,
            "messages": self.messages,
            "message_count": self.message_count,
            "doc_source": self.doc_source,
            "document_content": self.document_content,
            "timestamp": self.timestamp.isoformat(),
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionRecord":
        """Rehydrate a record from persisted data."""
        return cls(
            id=data["id"],
            title=data.get("title", "New Chat"),
            messages=list[MessagePayload](data.get("messages", [])),
            doc_source=data.get("doc_source"),
            document_content=data.get("document_content"),
            timestamp=_parse_datetime(data.get("timestamp")),
            saved_at=_parse_datetime(data.get("saved_at"), allow_none=True),
        )


@dataclass
class SessionSummary:
    """API-facing summary for a session."""

    id: str
    title: str
    message_count: int
    timestamp: datetime
    doc_source: Optional[str] = None
    persisted: bool = False


@dataclass
class SessionDetail:
    """Detailed session view."""

    id: str
    messages: list[MessagePayload]
    doc_source: Optional[str] = None
    document_content: Optional[str] = None


@dataclass
class DocumentLoadResult:
    """Result of loading a document into a session."""

    session_id: str
    source: str
    char_count: int
    message: str


def _parse_datetime(value: Any, allow_none: bool = False) -> Optional[datetime]:
    """Parse ISO timestamps while remaining backward compatible."""
    if value is None:
        return None if allow_none else datetime.utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None if allow_none else datetime.utcnow()
