"""Smoke tests for backend API routing boundaries."""

from datetime import datetime

from fastapi.testclient import TestClient

from agent_service.models import APIError
from finchat_backend.main import app
from finchat_backend.core.models import DocumentLoadResult, SessionDetail, SessionSummary


class TestBackendApi:
    """Verify routers delegate to service boundaries."""

    def test_sessions_route_uses_session_service(self, monkeypatch):
        from finchat_backend.api.v1 import sessions as sessions_api

        class StubSessionService:
            def list_sessions(self):
                return [
                    SessionSummary(
                        id="session-1",
                        title="First chat",
                        message_count=2,
                        timestamp=datetime(2024, 1, 1, 12, 0, 0),
                        doc_source="Uploaded: report.txt",
                        persisted=True,
                    )
                ]

        monkeypatch.setattr(sessions_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        assert response.json()[0]["id"] == "session-1"
        assert response.json()[0]["persisted"] is True

    def test_chat_route_returns_service_response(self, monkeypatch):
        from finchat_backend.api.v1 import chat as chat_api

        class StubSessionService:
            def chat(self, session_id: str, message: str) -> str:
                assert session_id == "session-1"
                assert message == "hello"
                return "assistant reply"

        monkeypatch.setattr(chat_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={"session_id": "session-1", "message": "hello"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "response": "assistant reply",
            "session_id": "session-1",
        }

    def test_chat_route_maps_api_error_to_bad_gateway(self, monkeypatch):
        from finchat_backend.api.v1 import chat as chat_api

        class StubSessionService:
            def chat(self, session_id: str, message: str) -> str:
                raise APIError("OpenRouter API error: invalid API key")

        monkeypatch.setattr(chat_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={"session_id": "session-1", "message": "hello"},
        )

        assert response.status_code == 502
        assert response.json()["detail"] == "OpenRouter API error: invalid API key"

    def test_chat_route_maps_auth_error_to_bad_gateway(self, monkeypatch):
        from finchat_backend.api.v1 import chat as chat_api

        class StubSessionService:
            def chat(self, session_id: str, message: str) -> str:
                raise APIError(
                    "OpenRouter authentication failed. "
                    "Please check `OPENROUTER_API_KEY` in your `.env` file."
                )

        monkeypatch.setattr(chat_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.post(
            "/api/v1/chat",
            json={"session_id": "session-1", "message": "hello"},
        )

        assert response.status_code == 502
        assert "OPENROUTER_API_KEY" in response.json()["detail"]

    def test_analyze_route_returns_agent_analysis(self, monkeypatch):
        from finchat_backend.api.v1 import chat as chat_api

        class StubAgent:
            def analyze_financials(self) -> str:
                return "analysis result"

        class StubSessionService:
            def require_session(self, session_id: str):
                assert session_id == "session-1"
                return StubAgent()

        monkeypatch.setattr(chat_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.post("/api/v1/sessions/session-1/analyze")

        assert response.status_code == 200
        assert response.json() == {
            "response": "analysis result",
            "session_id": "session-1",
        }

    def test_search_route_returns_formatted_results(self, monkeypatch):
        from finchat_backend.api.v1 import chat as chat_api
        from agent_service.models import SearchResult

        class StubAgent:
            def search_document(self, query: str):
                assert query == "revenue"
                return SearchResult(
                    query=query,
                    matches=[{"match": "Revenue", "context": "Revenue was $100"}],
                    total_matches=1,
                    displayed_matches=1,
                )

        class StubSessionService:
            def require_session(self, session_id: str):
                assert session_id == "session-1"
                return StubAgent()

        monkeypatch.setattr(chat_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.post(
            "/api/v1/sessions/session-1/search",
            json={"query": "revenue"},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session-1"
        assert "Revenue" in response.json()["result"]

    def test_upload_route_maps_document_service_result(self, monkeypatch):
        from finchat_backend.api.v1 import files as files_api

        class StubDocumentService:
            def load_upload(self, session_id: str, filename: str, content_bytes: bytes):
                assert session_id == "session-1"
                assert filename == "report.txt"
                assert content_bytes == b"hello"
                return DocumentLoadResult(
                    session_id="session-1",
                    source="Uploaded: report.txt",
                    char_count=5,
                    message="Loaded report.txt",
                )

        monkeypatch.setattr(files_api, "document_service", StubDocumentService())
        client = TestClient(app)

        response = client.post(
            "/api/v1/upload",
            data={"session_id": "session-1"},
            files={"file": ("report.txt", b"hello", "text/plain")},
        )

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "message": "Loaded report.txt",
            "session_id": "session-1",
            "char_count": 5,
        }

    def test_sync_session_route_updates_backend_state(self, monkeypatch):
        from finchat_backend.api.v1 import sessions as sessions_api

        class StubSessionService:
            def update_session_state(self, session_id: str, **kwargs):
                assert session_id == "session-1"
                assert kwargs["messages"][0]["content"] == "hello"
                assert kwargs["doc_source"] == "Uploaded: report.txt"
                assert kwargs["document_content"] == "Revenue"
                assert kwargs["persist"] is True

            def get_session_detail(self, session_id: str):
                return SessionDetail(
                    id=session_id,
                    messages=[{"role": "user", "content": "hello"}],
                    doc_source="Uploaded: report.txt",
                    document_content="Revenue",
                )

        monkeypatch.setattr(sessions_api, "session_service", StubSessionService())
        client = TestClient(app)

        response = client.put(
            "/api/v1/sessions/session-1",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "doc_source": "Uploaded: report.txt",
                "document_content": "Revenue",
                "persist": True,
            },
        )

        assert response.status_code == 200
        assert response.json()["document_content"] == "Revenue"
