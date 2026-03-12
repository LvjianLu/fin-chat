"""
File upload API endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from finchat_backend.core.agent_manager import session_service
from finchat_backend.core.errors import BackendConfigurationError, DocumentProcessingError
from finchat_backend.core.services.document_service import DocumentService

router = APIRouter()
document_service = DocumentService(session_service)

class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    char_count: int

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a document (txt, pdf, htm, html) and load it into the session."""
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_file"
        result = document_service.load_upload(session_id, filename, content_bytes)
        return UploadResponse(
            success=True,
            message=result.message,
            session_id=result.session_id,
            char_count=result.char_count
        )
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}/document")
async def clear_document(session_id: str):
    """Clear the document from a session."""
    try:
        document_service.clear_document(session_id)
        return {"status": "cleared", "session_id": session_id}
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
