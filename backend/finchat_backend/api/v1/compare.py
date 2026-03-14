"""Document comparison API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from finchat_backend.core.agent_manager import session_service
from finchat_backend.core.errors import BackendConfigurationError, DocumentProcessingError
from finchat_backend.core.services.document_comparison_service import DocumentComparisonService
from finchat_backend.core.models import DocumentComparisonResult


router = APIRouter()


class CompareRequest(BaseModel):
    """Request model for document comparison."""
    query: Optional[str] = Field(None, description="Optional specific comparison query")


class CompareResponse(BaseModel):
    """Response model for document comparison."""
    document_count: int
    documents: List[dict[str, Any]]
    comparison_summary: str
    query: Optional[str] = None


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(
    files: List[UploadFile] = File(..., description="Documents to compare"),
    query: Optional[str] = Query(None, description="Optional comparison query")
):
    """Compare multiple documents.

    Supports up to 5 documents at once. Documents can be of different types
    (txt, pdf, html, json, csv). The comparison will analyze similarities
    and differences between the documents.
    """
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 documents are required for comparison"
        )
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 documents can be compared at once"
        )

    try:
        # Read all files
        documents = []
        for file in files:
            content_bytes = await file.read()
            filename = file.filename or "unnamed"
            documents.append((filename, content_bytes))

        # Perform comparison
        comparison_service = DocumentComparisonService()
        result: DocumentComparisonResult = comparison_service.compare_documents(
            documents=documents,
            query=query
        )

        return CompareResponse(**result.to_dict())

    except DocumentProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except BackendConfigurationError as exc:
        raise HTTPException(status_code=500, detail=f"Backend not initialized: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
