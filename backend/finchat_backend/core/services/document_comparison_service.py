"""Document comparison service for comparing multiple documents."""

from __future__ import annotations

from typing import List, Optional

from finchat_backend.core.errors import DocumentProcessingError
from finchat_backend.core.extractors.base import TextExtractor
from finchat_backend.core.extractors.csv import CsvTextExtractor
from finchat_backend.core.extractors.html import HtmlTextExtractor
from finchat_backend.core.extractors.json import JsonTextExtractor
from finchat_backend.core.extractors.pdf import PdfTextExtractor
from finchat_backend.core.extractors.text import PlainTextExtractor
from finchat_backend.core.models import DocumentComparisonResult
from finchat_backend.agent_service.agent.llm.openrouter import OpenRouterLLM
from finchat_backend.agent_service.config import Settings


class DocumentComparisonService:
    """Service for comparing multiple documents."""

    def __init__(
        self,
        llm: Optional[OpenRouterLLM] = None,
        settings: Optional[Settings] = None,
        extractors: Optional[List[TextExtractor]] = None,
    ):
        """Initialize the comparison service.

        Args:
            llm: LLM provider for generating comparisons (optional)
            settings: Application settings (optional, used if llm not provided)
            extractors: List of text extractors (uses defaults if None)
        """
        self.llm = llm
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
        raise DocumentProcessingError(f"Unsupported file type: {filename}")

    def extract_document(self, filename: str, content_bytes: bytes) -> str:
        """Extract text from a document."""
        extractor = self._get_extractor(filename)
        try:
            return extractor.extract(content_bytes)
        except Exception as exc:
            raise DocumentProcessingError(
                f"Failed to extract text from {filename}: {exc}"
            ) from exc

    def compare_documents(
        self,
        documents: List[tuple[str, bytes]],
        query: Optional[str] = None,
    ) -> DocumentComparisonResult:
        """Compare multiple documents.

        Args:
            documents: List of (filename, content_bytes) tuples
            query: Optional specific comparison query/focus

        Returns:
            DocumentComparisonResult with comparison summary
        """
        if len(documents) < 2:
            raise ValueError("At least 2 documents are required for comparison")
        if len(documents) > 5:
            raise ValueError("Maximum 5 documents can be compared at once")

        # Extract text from all documents
        extracted_docs = []
        for filename, content_bytes in documents:
            text = self.extract_document(filename, content_bytes)
            extracted_docs.append({
                "filename": filename,
                "content": text,
                "char_count": len(text),
            })

        # Generate comparison using LLM or rule-based approach
        comparison = self._generate_comparison(extracted_docs, query)

        return DocumentComparisonResult(
            document_count=len(extracted_docs),
            documents=[{
                "filename": doc["filename"],
                "char_count": doc["char_count"],
            } for doc in extracted_docs],
            comparison_summary=comparison,
            query=query,
        )

    def _generate_comparison(
        self,
        documents: List[dict],
        query: Optional[str] = None,
    ) -> str:
        """Generate comparison text using LLM or fallback."""
        if self.llm and query:
            return self._llm_comparison(documents, query)
        elif self.llm:
            return self._llm_general_comparison(documents)
        else:
            return self._basic_comparison(documents)

    def _llm_comparison(self, documents: List[dict], query: str) -> str:
        """Use LLM to generate focused comparison."""
        prompt = self._build_comparison_prompt(documents, query)
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            return response if isinstance(response, str) else str(response)
        except Exception as e:
            # Fallback to basic comparison on LLM failure
            return f"LLM comparison failed: {e}\n\n" + self._basic_comparison(documents)

    def _llm_general_comparison(self, documents: List[dict]) -> str:
        """Use LLM to generate general comparison."""
        prompt = self._build_general_comparison_prompt(documents)
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            return response if isinstance(response, str) else str(response)
        except Exception as e:
            return f"LLM comparison failed: {e}\n\n" + self._basic_comparison(documents)

    def _build_comparison_prompt(self, documents: List[dict], query: str) -> str:
        """Build prompt for focused comparison."""
        prompt = f"""Compare the following {len(documents)} documents based on: {query}

Documents:
"""
        for i, doc in enumerate(documents, 1):
            prompt += f"\n--- Document {i}: {doc['filename']} ({doc['char_count']} chars) ---\n"
            preview = doc['content'][:2000] + ("..." if len(doc['content']) > 2000 else "")
            prompt += preview + "\n"

        prompt += f"""

Please provide a detailed comparison focusing on: {query}

Structure your response with:
1. Overview of each document
2. Key similarities
3. Key differences
4. Conclusions or insights
"""
        return prompt

    def _build_general_comparison_prompt(self, documents: List[dict]) -> str:
        """Build prompt for general comparison."""
        prompt = f"""Provide a general comparison of the following {len(documents)} documents:

"""
        for i, doc in enumerate(documents, 1):
            preview = doc['content'][:2000] + ("..." if len(doc['content']) > 2000 else "")
            prompt += f"\n--- Document {i}: {doc['filename']} ({doc['char_count']} chars) ---\n"
            prompt += preview + "\n"

        prompt += """

Please provide:
1. Overview of each document's content and purpose
2. Key similarities across documents
3. Key differences between documents
4. Notable patterns or insights
"""
        return prompt

    def _basic_comparison(self, documents: List[dict]) -> str:
        """Generate basic comparison without LLM."""
        lines = [
            f"Document Comparison ({len(documents)} documents)",
            "=" * 50,
        ]

        for i, doc in enumerate(documents, 1):
            lines.append(f"\nDocument {i}: {doc['filename']}")
            lines.append(f"  Character count: {doc['char_count']:,}")
            preview = doc['content'][:200]
            if len(doc['content']) > 200:
                preview += "..."
            lines.append(f"  Preview: {preview}")

        lines.append("\n" + "=" * 50)
        lines.append("Basic statistics:")
        lengths = [doc['char_count'] for doc in documents]
        lines.append(f"  Total characters: {sum(lengths):,}")
        lines.append(f"  Average length: {sum(lengths) // len(lengths):,}")
        lines.append(f"  Shortest: {min(lengths):,} chars")
        lines.append(f"  Longest: {max(lengths):,} chars")

        return "\n".join(lines)
