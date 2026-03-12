"""Tests for backend session orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from finchat.agent.memory import ConversationMemory
from finchat_backend.core.models import SessionRecord
from finchat_backend.core.repositories.base import SessionRepository
from finchat_backend.core.services.session_service import SessionService


@dataclass
class StubAgent:
    """Minimal agent stub for session service tests."""

    memory: ConversationMemory

    def chat(self, message: str) -> str:
        response = f"echo:{message}"
        self.memory.add_message("user", message)
        self.memory.add_message("assistant", response)
        return response

    def load_document(self, text: str, source: str) -> str:
        self.memory.set_document(text, source)
        return source

    def clear_document(self) -> str:
        self.memory.clear_document()
        return "Document cleared"


class StubFactory:
    """Factory that builds stub agents without external dependencies."""

    def create_agent(self, messages=None, document_context=None, doc_source=None):
        memory = ConversationMemory()
        if document_context and doc_source:
            memory.set_document(document_context, doc_source)
        for message in messages or []:
            memory.add_message(message["role"], message["content"])
        return StubAgent(memory=memory)


class InMemorySessionRepository(SessionRepository):
    """Simple in-memory repository for service tests."""

    def __init__(self):
        self.records: dict[str, SessionRecord] = {}

    def save_session(self, record: SessionRecord) -> bool:
        self.records[record.id] = SessionRecord.from_dict(record.to_dict())
        return True

    def load_session(self, session_id: str):
        return self.records.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self.records.pop(session_id, None) is not None

    def list_sessions(self):
        return sorted(
            self.records.values(),
            key=lambda record: record.timestamp,
            reverse=True,
        )

    def session_exists(self, session_id: str) -> bool:
        return session_id in self.records


class TestSessionService:
    """Verify session metadata, persistence, and restore flow."""

    def build_service(self):
        return SessionService(
            repository=InMemorySessionRepository(),
            factory=StubFactory(),
            settings=object(),
        )

    def test_create_and_chat_updates_summary(self):
        service = self.build_service()

        created = service.create_session()
        response = service.chat(created.id, "hello world")
        sessions = service.list_sessions()

        assert response == "echo:hello world"
        assert sessions[0].id == created.id
        assert sessions[0].title == "hello world"
        assert sessions[0].message_count == 2
        assert sessions[0].persisted is False

    def test_save_and_reload_session(self):
        repository = InMemorySessionRepository()
        service = SessionService(repository=repository, factory=StubFactory(), settings=object())
        created = service.create_session()
        service.chat(created.id, "persist me")

        assert service.save_session(created.id) is True

        restored = SessionService(repository=repository, factory=StubFactory(), settings=object())
        assert restored.load_session(created.id) is True
        detail = restored.get_session_detail(created.id)

        assert detail.messages[0]["content"] == "persist me"
        assert detail.messages[1]["content"] == "echo:persist me"

    def test_list_sessions_preserves_persisted_doc_source(self):
        repository = InMemorySessionRepository()
        repository.save_session(
            SessionRecord(
                id="persisted-1",
                title="Saved chat",
                messages=[{"role": "user", "content": "show filing"}],
                doc_source="SEC: AAPL 10-K",
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
            )
        )
        service = SessionService(repository=repository, factory=StubFactory(), settings=object())

        sessions = service.list_sessions()

        assert sessions[0].id == "persisted-1"
        assert sessions[0].doc_source == "SEC: AAPL 10-K"
        assert sessions[0].persisted is True

    def test_update_session_state_restores_messages_and_document(self):
        service = self.build_service()
        created = service.create_session()

        record = service.update_session_state(
            created.id,
            messages=[
                {"role": "user", "content": "question"},
                {"role": "assistant", "content": "answer"},
            ],
            doc_source="Uploaded: report.txt",
            document_content="Revenue was $100 million.",
            persist=True,
        )
        detail = service.get_session_detail(created.id)

        assert record.saved_at is not None
        assert detail.messages[0]["content"] == "question"
        assert detail.doc_source == "Uploaded: report.txt"
        assert detail.document_content == "Revenue was $100 million."
