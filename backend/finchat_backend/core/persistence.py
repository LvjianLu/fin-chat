"""Backward-compatible persistence entrypoint."""

from finchat_backend.core.repositories.file_session_repository import FileSessionRepository


class SessionPersistence(FileSessionRepository):
    """Compatibility alias for the file-backed session repository."""
