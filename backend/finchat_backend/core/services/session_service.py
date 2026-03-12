"""Session lifecycle service for backend routes."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Optional

from finchat_backend.core.bootstrap import ensure_project_path

ensure_project_path()

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

from agent_service.agent.agent import FinChat
from agent_service.config import Settings, load_settings_from_dict
from finchat_backend.core.errors import (
    BackendConfigurationError,
    SessionNotFoundError,
)
from finchat_backend.core.factories.agent_factory import FinChatAgentFactory
from finchat_backend.core.models import SessionDetail, SessionRecord, SessionSummary
from finchat_backend.core.repositories.base import SessionRepository
from finchat_backend.core.repositories.file_session_repository import FileSessionRepository


class SessionService:
    """Own session state, persistence, and agent lifecycle."""

    def __init__(
        self,
        repository: Optional[SessionRepository] = None,
        factory: Optional[FinChatAgentFactory] = None,
        settings: Optional[Settings] = None,
    ):
        load_dotenv()
        self._repository = repository
        self._factory = factory
        self._settings = settings
        self._agents: dict[str, FinChat] = {}
        self._records: dict[str, SessionRecord] = {}
        self._initialized = settings is not None and repository is not None and factory is not None
        if self._initialized:
            self._load_persisted_sessions()

    @property
    def agents(self) -> dict[str, FinChat]:
        """Expose in-memory agents for compatibility/testing."""
        self._ensure_initialized()
        return self._agents

    @property
    def repository(self) -> SessionRepository:
        """Return the initialized session repository."""
        self._ensure_initialized()
        assert self._repository is not None
        return self._repository

    @property
    def settings(self) -> Settings:
        """Return initialized backend settings."""
        self._ensure_initialized()
        assert self._settings is not None
        return self._settings

    def _ensure_initialized(self) -> None:
        """Lazily initialize settings, repository, and persisted sessions."""
        if self._initialized:
            return

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")
        if not api_key:
            raise BackendConfigurationError("OPENROUTER_API_KEY not set in environment")

        self._settings = load_settings_from_dict(
            {
                "openrouter_api_key": api_key,
                "openrouter_model": model,
            }
        )
        self._repository = self._repository or FileSessionRepository(
            data_dir=self._settings.data_dir
        )
        self._factory = self._factory or FinChatAgentFactory(self._settings)
        self._load_persisted_sessions()
        self._initialized = True

    def _load_persisted_sessions(self) -> None:
        """Restore persisted sessions into memory on first startup."""
        assert self._repository is not None
        for record in self._repository.list_sessions():
            self._records[record.id] = record
            if record.id not in self._agents:
                self._agents[record.id] = self._build_agent_from_record(record)

    def _build_agent_from_record(self, record: SessionRecord) -> FinChat:
        """Create a runtime agent from a session record."""
        assert self._factory is not None
        return self._factory.create_agent(
            messages=record.messages,
            document_context=record.document_content,
            doc_source=record.doc_source,
        )

    def _default_title(self, messages: list[dict[str, str]]) -> str:
        """Derive a session title from the first user message."""
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                return f"{content[:30]}..." if len(content) > 30 else content
        return "New Chat"

    def _sync_record(
        self,
        session_id: str,
        *,
        timestamp: Optional[datetime] = None,
        fallback_doc_source: Optional[str] = None,
    ) -> SessionRecord:
        """Update the cached record from the in-memory agent state."""
        agent = self.get_or_create_agent(session_id)
        history = [message.to_dict() for message in agent.memory.get_history()]
        doc_meta = agent.memory.get_document_metadata()
        document_content = agent.memory.get_document_context() or None
        existing = self._records.get(session_id)
        doc_source = (
            doc_meta.source_name
            if doc_meta
            else fallback_doc_source
            or (existing.doc_source if existing else None)
        )
        record = SessionRecord(
            id=session_id,
            title=self._default_title(history),
            messages=history,
            doc_source=doc_source,
            document_content=document_content
            or (existing.document_content if existing else None),
            timestamp=timestamp or (existing.timestamp if existing else datetime.utcnow()),
            saved_at=existing.saved_at if existing else None,
        )
        self._records[session_id] = record
        return record

    def is_ready(self) -> bool:
        """Report whether required environment configuration exists."""
        return bool(os.getenv("OPENROUTER_API_KEY"))

    def get_or_create_agent(self, session_id: str) -> FinChat:
        """Return the current session agent, creating it when missing."""
        self._ensure_initialized()
        if session_id not in self._agents:
            assert self._factory is not None
            self._agents[session_id] = self._factory.create_agent()
            self._records.setdefault(
                session_id,
                SessionRecord(id=session_id, title="New Chat"),
            )
        return self._agents[session_id]

    def create_session(self) -> SessionSummary:
        """Create a new empty session."""
        session_id = str(uuid.uuid4())
        self.get_or_create_agent(session_id)
        record = self._sync_record(session_id, timestamp=datetime.utcnow())
        return self._to_summary(record)

    def remove_agent(self, session_id: str) -> None:
        """Remove a session from memory only."""
        agent = self._agents.pop(session_id, None)
        if agent:
            try:
                agent.clear_document()
            except Exception:
                pass
        self._records.pop(session_id, None)

    def delete_session(self, session_id: str) -> None:
        """Delete a session from memory."""
        self.remove_agent(session_id)

    def get_session_detail(self, session_id: str) -> SessionDetail:
        """Return messages and document info for a session."""
        record = self._sync_record(session_id)
        return SessionDetail(
            id=record.id,
            messages=record.messages,
            doc_source=record.doc_source,
            document_content=record.document_content,
        )

    def get_session_history(self, session_id: str) -> list[dict[str, str]]:
        """Return serialized session history."""
        return self._sync_record(session_id).messages

    def chat(self, session_id: str, message: str) -> str:
        """Send a message through the session runtime."""
        response = self.get_or_create_agent(session_id).chat(message)
        self._sync_record(session_id, timestamp=datetime.utcnow())
        return response

    def clear_history(self, session_id: str) -> None:
        """Clear chat history for a session."""
        agent = self.get_or_create_agent(session_id)
        agent.memory.clear_history()
        self._sync_record(session_id, timestamp=datetime.utcnow())

    def reset_session(self, session_id: str) -> None:
        """Clear both chat history and loaded document."""
        agent = self.get_or_create_agent(session_id)
        agent.clear_document()
        agent.memory.clear_history()
        self._sync_record(
            session_id,
            timestamp=datetime.utcnow(),
            fallback_doc_source=None,
        )

    def clear_document(self, session_id: str) -> None:
        """Clear only the current document from a session."""
        agent = self.get_or_create_agent(session_id)
        agent.clear_document()
        self._sync_record(
            session_id,
            timestamp=datetime.utcnow(),
            fallback_doc_source=None,
        )

    def mark_document_loaded(self, session_id: str, source: str) -> SessionRecord:
        """Refresh metadata after a document load."""
        return self._sync_record(
            session_id,
            timestamp=datetime.utcnow(),
            fallback_doc_source=source,
        )

    def list_sessions(self) -> list[SessionSummary]:
        """List all in-memory sessions."""
        self._ensure_initialized()
        for session_id in list(self._agents):
            self._sync_record(session_id)
        sessions = [self._to_summary(record) for record in self._records.values()]
        sessions.sort(key=lambda session: session.timestamp, reverse=True)
        return sessions

    def save_session(self, session_id: str) -> bool:
        """Persist a session to the repository."""
        record = self._sync_record(session_id, timestamp=datetime.utcnow())
        record.saved_at = datetime.utcnow()
        self._records[session_id] = record
        return self.repository.save_session(record)

    def update_session_state(
        self,
        session_id: str,
        *,
        messages: list[dict[str, str]],
        doc_source: Optional[str] = None,
        document_content: Optional[str] = None,
        persist: bool = True,
    ) -> SessionRecord:
        """Replace backend session state from a client payload."""
        self._ensure_initialized()
        existing = self._records.get(session_id)
        record = SessionRecord(
            id=session_id,
            title=self._default_title(messages),
            messages=list(messages),
            doc_source=doc_source or (existing.doc_source if existing else None),
            document_content=(
                document_content
                if document_content is not None
                else (existing.document_content if existing else None)
            ),
            timestamp=datetime.utcnow(),
            saved_at=existing.saved_at if existing else None,
        )
        self._records[session_id] = record
        self._agents[session_id] = self._build_agent_from_record(record)
        if persist:
            record.saved_at = datetime.utcnow()
            self._records[session_id] = record
            self.repository.save_session(record)
        return record

    def load_session(self, session_id: str) -> bool:
        """Load a session from persistence into memory."""
        record = self.repository.load_session(session_id)
        if record is None:
            return False
        self._records[session_id] = record
        self._agents[session_id] = self._build_agent_from_record(record)
        return True

    def list_persisted_sessions(self) -> list[SessionRecord]:
        """List persisted sessions from the repository."""
        self._ensure_initialized()
        return self.repository.list_sessions()

    def delete_persisted_session(self, session_id: str) -> bool:
        """Delete a persisted session and unload it if present."""
        self._ensure_initialized()
        self._agents.pop(session_id, None)
        self._records.pop(session_id, None)
        return self.repository.delete_session(session_id)

    def require_session(self, session_id: str) -> FinChat:
        """Return an existing session or raise if it cannot be resolved."""
        try:
            return self.get_or_create_agent(session_id)
        except BackendConfigurationError as exc:
            raise exc
        except Exception as exc:
            raise SessionNotFoundError(f"Session {session_id} not found") from exc

    def _to_summary(self, record: SessionRecord) -> SessionSummary:
        """Map a session record to a summary DTO."""
        return SessionSummary(
            id=record.id,
            title=record.title,
            message_count=record.message_count,
            timestamp=record.timestamp,
            doc_source=record.doc_source,
            persisted=self.repository.session_exists(record.id),
        )
