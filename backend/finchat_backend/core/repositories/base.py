"""Repository abstractions for backend persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from finchat_backend.core.models import SessionRecord


class SessionRepository(ABC):
    """Abstract session persistence contract."""

    @abstractmethod
    def save_session(self, record: SessionRecord) -> bool:
        """Persist a session record."""

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[SessionRecord]:
        """Load a session by id."""

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by id."""

    @abstractmethod
    def list_sessions(self) -> list[SessionRecord]:
        """List all persisted sessions."""

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check whether a persisted session exists."""
