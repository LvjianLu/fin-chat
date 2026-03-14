"""Document ingestion service for backend routes."""

from __future__ import annotations

from typing import Iterable, Optional

from finchat_backend.core.errors import DocumentProcessingError
from finchat_backend.core.extractors.base import TextExtractor
from finchat_backend.core.extractors.csv import CsvTextExtractor
from finchat_backend.core.extractors.html import HtmlTextExtractor
from finchat_backend.core.extractors.json import JsonTextExtractor
from finchat_backend.core.extractors.pdf import PdfTextExtractor
from finchat_backend.core.extractors.text import PlainTextExtractor
from finchat_backend.core.models import DocumentLoadResult
from finchat_backend.core.services.session_service import SessionService


class DocumentService:
    """Handle document extraction and loading into session runtimes."""

    def __init__(
        self,
        session_service: SessionService,
        extractors: Optional[Iterable[TextExtractor]] = None,
    ):
        self.session_service = session_service
        self.extractors = list(
            extractors
            or (
                PlainTextExtractor(),
                PdfTextExtractor(),
                HtmlTextExtractor(),
                JsonTextExtractor(),
                CsvTextExtractor(),
            )
        )

    def _get_extractor(self, filename: str) -> TextExtractor:
        """Resolve an extractor by file name."""
        for extractor in self.extractors:
            if extractor.can_handle(filename):
                return extractor
        raise DocumentProcessingError("Unsupported file type")

    def load_upload(
        self,
        session_id: str,
        filename: str,
        content_bytes: bytes,
    ) -> DocumentLoadResult:
        """Extract text from an upload and load it into the session."""
        extractor = self._get_extractor(filename)
        try:
            content = extractor.extract(content_bytes)
        except Exception as exc:
            raise DocumentProcessingError(f"Failed to process {filename}") from exc

        source = f"Uploaded: {filename}"
        agent = self.session_service.get_or_create_agent(session_id)
        agent.load_document(content, source)
        self.session_service.mark_document_loaded(session_id, source)
        return DocumentLoadResult(
            session_id=session_id,
            source=source,
            char_count=len(content),
            message=f"Loaded {filename}",
        )

    def clear_document(self, session_id: str) -> None:
        """Clear the loaded document from a session."""
        self.session_service.clear_document(session_id)
