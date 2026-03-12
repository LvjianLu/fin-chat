"""Tests for the file-backed session repository."""

from datetime import datetime, timedelta

from finchat_backend.core.models import SessionRecord
from finchat_backend.core.repositories.file_session_repository import (
    FileSessionRepository,
)


class TestFileSessionRepository:
    """Verify JSON persistence stays backward compatible."""

    def test_save_and_load_session(self, tmp_path):
        repository = FileSessionRepository(data_dir=str(tmp_path))
        record = SessionRecord(
            id="session-1",
            title="First chat",
            messages=[{"role": "user", "content": "hello"}],
            doc_source="Uploaded: sample.txt",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            saved_at=datetime(2024, 1, 1, 12, 5, 0),
        )

        assert repository.save_session(record) is True

        loaded = repository.load_session("session-1")

        assert loaded is not None
        assert loaded.id == "session-1"
        assert loaded.title == "First chat"
        assert loaded.messages == [{"role": "user", "content": "hello"}]
        assert loaded.doc_source == "Uploaded: sample.txt"
        assert loaded.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert loaded.saved_at == datetime(2024, 1, 1, 12, 5, 0)

    def test_list_sessions_is_sorted_descending(self, tmp_path):
        repository = FileSessionRepository(data_dir=str(tmp_path))
        older = SessionRecord(
            id="older",
            title="Older",
            timestamp=datetime.utcnow() - timedelta(days=1),
        )
        newer = SessionRecord(
            id="newer",
            title="Newer",
            timestamp=datetime.utcnow(),
        )

        repository.save_session(older)
        repository.save_session(newer)

        sessions = repository.list_sessions()

        assert [session.id for session in sessions] == ["newer", "older"]

    def test_delete_session_removes_file(self, tmp_path):
        repository = FileSessionRepository(data_dir=str(tmp_path))
        record = SessionRecord(id="session-1", title="To delete")
        repository.save_session(record)

        assert repository.delete_session("session-1") is True
        assert repository.load_session("session-1") is None
