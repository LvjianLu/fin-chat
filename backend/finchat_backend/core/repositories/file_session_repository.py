"""File-backed session repository."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from finchat_backend.core.errors import SessionPersistenceError
from finchat_backend.core.models import SessionRecord
from finchat_backend.core.repositories.base import SessionRepository

logger = logging.getLogger(__name__)


class FileSessionRepository(SessionRepository):
    """Persist sessions as JSON files under the data directory."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_file_path(self, session_id: str) -> Path:
        """Return the path for a persisted session."""
        return self.sessions_dir / f"{session_id}.json"

    def save_session(self, record: SessionRecord) -> bool:
        """Persist a session record to disk."""
        file_path = self._session_file_path(record.id)
        payload = record.to_dict()
        try:
            with file_path.open("w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj, indent=2)
        except OSError as exc:
            logger.error("Failed to save session %s", record.id, exc_info=True)
            raise SessionPersistenceError(f"Failed to save session {record.id}") from exc
        return True

    def load_session(self, session_id: str) -> Optional[SessionRecord]:
        """Load a session record from disk."""
        file_path = self._session_file_path(session_id)
        if not file_path.exists():
            return None

        try:
            with file_path.open("r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load session %s", session_id, exc_info=True)
            raise SessionPersistenceError(f"Failed to load session {session_id}") from exc

        return SessionRecord.from_dict(payload)

    def delete_session(self, session_id: str) -> bool:
        """Delete a persisted session."""
        file_path = self._session_file_path(session_id)
        if not file_path.exists():
            return False

        try:
            file_path.unlink()
        except OSError as exc:
            logger.error("Failed to delete session %s", session_id, exc_info=True)
            raise SessionPersistenceError(f"Failed to delete session {session_id}") from exc
        return True

    def list_sessions(self) -> list[SessionRecord]:
        """Return all persisted sessions sorted by timestamp desc."""
        sessions: list[SessionRecord] = []
        for file_path in self.sessions_dir.glob("*.json"):
            try:
                with file_path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
                sessions.append(SessionRecord.from_dict(payload))
            except (OSError, json.JSONDecodeError):
                logger.warning("Failed to read session file %s", file_path, exc_info=True)

        sessions.sort(key=lambda record: record.timestamp or datetime.utcnow(), reverse=True)
        return sessions

    def session_exists(self, session_id: str) -> bool:
        """Return whether a session file exists."""
        return self._session_file_path(session_id).exists()
