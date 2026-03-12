"""
Session management API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from finchat_backend.core.agent_manager import session_service
from finchat_backend.core.errors import BackendConfigurationError

router = APIRouter()

class SessionInfo(BaseModel):
    id: str
    title: str
    message_count: int
    timestamp: datetime
    doc_source: Optional[str] = None
    persisted: bool = False  # Whether this session is saved to disk

class SessionDetail(BaseModel):
    id: str
    messages: List[dict]
    doc_source: Optional[str] = None
    document_content: Optional[str] = None


class SyncSessionRequest(BaseModel):
    messages: List[dict]
    doc_source: Optional[str] = None
    document_content: Optional[str] = None
    persist: bool = True

class PersistedSessionInfo(BaseModel):
    id: str
    title: str
    message_count: int
    timestamp: datetime
    doc_source: Optional[str] = None
    saved_at: datetime

@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List all conversation sessions (includes auto-loaded persisted ones)."""
    try:
        sessions = session_service.list_sessions()
        return [SessionInfo(**session.__dict__) for session in sessions]
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")

@router.post("/sessions", response_model=SessionInfo)
async def create_session():
    """Create a new conversation session."""
    try:
        session = session_service.create_session()
        return SessionInfo(**session.__dict__)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")

@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """Get a specific session's details."""
    try:
        session = session_service.get_session_detail(session_id)
        return SessionDetail(**session.__dict__)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")


@router.put("/sessions/{session_id}", response_model=SessionDetail)
async def sync_session(session_id: str, request: SyncSessionRequest):
    """Sync a client-side session state into the backend."""
    try:
        session_service.update_session_state(
            session_id,
            messages=request.messages,
            doc_source=request.doc_source,
            document_content=request.document_content,
            persist=request.persist,
        )
        session = session_service.get_session_detail(session_id)
        return SessionDetail(**session.__dict__)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    session_service.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}

@router.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a session (clear history and document)."""
    try:
        session_service.reset_session(session_id)
        return {"status": "reset", "session_id": session_id}
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")

@router.get("/persisted-sessions", response_model=List[PersistedSessionInfo])
async def list_persisted_sessions():
    """List all sessions saved to disk (persisted across restarts)."""
    try:
        sessions = session_service.list_persisted_sessions()
        return [
            PersistedSessionInfo(
                id=session.id,
                title=session.title,
                message_count=session.message_count,
                timestamp=session.timestamp,
                doc_source=session.doc_source,
                saved_at=session.saved_at or session.timestamp,
            )
            for session in sessions
        ]
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")

@router.post("/sessions/{session_id}/persist")
async def persist_session(session_id: str):
    """Save a session to disk (persist it)."""
    try:
        success = session_service.save_session(session_id)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    if success:
        return {"status": "saved", "session_id": session_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save session")

@router.post("/persisted-sessions/{session_id}/load")
async def load_persisted_session(session_id: str):
    """Load a persisted session into memory (restore from disk)."""
    try:
        success = session_service.load_session(session_id)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    if success:
        return {"status": "loaded", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Persisted session not found or failed to load")

@router.delete("/persisted-sessions/{session_id}")
async def delete_persisted_session(session_id: str):
    """Delete a session from disk."""
    try:
        success = session_service.delete_persisted_session(session_id)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    if success:
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Persisted session not found")
