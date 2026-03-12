"""Document search tool for finding terms in loaded documents."""

import json
import logging
from typing import Any, Dict

from .base import Tool, ToolResult
from agent_service.core.analyzer import FinDataExtractor
from agent_service.models import SearchResult

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    """Tool for searching within a loaded document.

    This tool searches for specific terms or patterns in the currently
    loaded document context. It uses FinDataExtractor to find
    matches with surrounding context.
    """

    def __init__(self, memory):
        """Initialize document search tool.

        Args:
            memory: ConversationMemory instance to access document context
        """
        self.memory = memory
        self.extractor = FinDataExtractor()

    @property
    def name(self) -> str:
        """Return tool identifier."""
        return "search_document"

    @property
    def description(self) -> str:
        """Return tool description for LLM."""
        return "Search for specific terms or numbers in the loaded financial document. Use this to find occurrences of keywords, figures, or metrics."

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for search tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - the term or phrase to find in the document"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str) -> ToolResult:
        """Execute document search.

        Args:
            query: Search query string

        Returns:
            ToolResult with SearchResult data on success, or error on failure
        """
        try:
            if not self.memory.has_document():
                return ToolResult(
                    success=False,
                    error="No document loaded. Please load a document first."
                )

            doc_context = self.memory.get_document_context()
            if not doc_context:
                return ToolResult(
                    success=False,
                    error="Document context is empty."
                )

            # Perform search using FinDataExtractor
            matches = self.extractor.extract_numbers_with_context(doc_context, query)

            # Build SearchResult object
            search_result = SearchResult(
                query=query,
                matches=matches,
                total_matches=len(matches),
                displayed_matches=min(len(matches), 5),
            )

            logger.info(
                "Document search completed",
                extra={"query": query, "matches_found": len(matches)}
            )

            return ToolResult(success=True, data=search_result)

        except Exception as e:
            logger.error("Document search failed", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
