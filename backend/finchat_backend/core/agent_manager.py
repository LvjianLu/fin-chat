"""Backward-compatible facade over the new session service."""

from finchat_backend.core.models import SessionRecord
from finchat_backend.core.services.session_service import SessionService


class AgentManager:
    """Compatibility wrapper around `SessionService`."""

    def __init__(self, session_service: SessionService):
        self._service = session_service

    @property
    def _agents(self):
        return self._service.agents

    @property
    def _persistence(self):
        return self._service.repository

    def _ensure_initialized(self) -> None:
        self._service._ensure_initialized()

    def get_or_create_agent(self, session_id: str):
        return self._service.get_or_create_agent(session_id)

    def save_session(self, session_id: str) -> bool:
        return self._service.save_session(session_id)

    def load_session(self, session_id: str) -> bool:
        return self._service.load_session(session_id)

    def get_persisted_sessions_info(self) -> list[SessionRecord]:
        return self._service.list_persisted_sessions()

    def delete_persisted_session(self, session_id: str) -> bool:
        return self._service.delete_persisted_session(session_id)

    def remove_agent(self, session_id: str) -> None:
        self._service.remove_agent(session_id)

    def is_ready(self) -> bool:
        return self._service.is_ready()


session_service = SessionService()
agent_manager = AgentManager(session_service)
