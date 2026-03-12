"""
Chat API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent_service.models import APIError
from finchat_backend.core.agent_manager import session_service
from finchat_backend.core.errors import BackendConfigurationError

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str


class AnalyzeResponse(BaseModel):
    response: str
    session_id: str


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    result: str
    session_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the chatbot and get a response."""
    try:
        response = session_service.chat(request.session_id, request.message)
        return ChatResponse(response=response, session_id=request.session_id)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/analyze", response_model=AnalyzeResponse)
async def analyze_document(session_id: str):
    """Analyze the currently loaded document for a session."""
    try:
        agent = session_service.require_session(session_id)
        response = agent.analyze_financials()
        return AnalyzeResponse(response=response, session_id=session_id)
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/search", response_model=SearchResponse)
async def search_document(session_id: str, request: SearchRequest):
    """Search the currently loaded document for a session."""
    try:
        agent = session_service.require_session(session_id)
        result = agent.search_document(request.query)
        return SearchResponse(
            result=result.format_results(),
            session_id=session_id,
        )
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    try:
        return {
            "session_id": session_id,
            "messages": session_service.get_session_history(session_id),
        }
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}/history")
async def clear_session_history(session_id: str):
    """Clear conversation history for a session (but keep document if loaded)."""
    try:
        session_service.clear_history(session_id)
        return {"status": "cleared", "session_id": session_id}
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
