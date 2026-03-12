"""Agent base class and FinChat implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TYPE_CHECKING

from .llm import LLMProvider
from .memory import ConversationMemory
from ..core.analyzer import FinDataExtractor
from ..models import ChatMessage, DocumentMetadata, SearchResult
from ..constants import CONVERSATION_HISTORY_MAX_EXCHANGES

if TYPE_CHECKING:
    from .tools.base import Tool

logger = logging.getLogger(__name__)

class Agent(ABC):
    """Abstract base class for agents."""

    @abstractmethod
    def run(self, user_input: str) -> str:
        """Process user input and return response.

        Args:
            user_input: User's question or message

        Returns:
            Agent's response text
        """
        pass

    @abstractmethod
    def load_document(self, text: str, source: str) -> str:
        """Load a document into the agent's context.

        Args:
            text: Document content
            source: Document source name

        Returns:
            Success message
        """
        pass

    @abstractmethod
    def clear_document(self) -> str:
        """Clear the current document context.

        Returns:
            Confirmation message
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if agent is ready to process queries.

        Returns:
            True if agent is ready, False otherwise
        """
        pass


class FinChat(Agent):
    """Financial analysis chat agent with LLM, memory, and tools.

    This agent specializes in analyzing financial statements and SEC filings.
    It uses an LLM provider for reasoning, maintains conversation memory,
    and can utilize various tools for document operations.
    """

    SYSTEM_PROMPT = """You are a financial analyst assistant specializing in SEC filings and financial statement analysis.

Your capabilities:
- Analyze financial statements (10-K, 10-Q, 8-K)
- Extract and explain key financial metrics
- Answer questions about revenue, income, assets, liabilities, cash flow
- Provide insights on financial trends and ratios
- Explain accounting concepts in simple terms

Guidelines:
1. Always base your answers on the provided document context
2. If information is not available, state that clearly
3. Use bullet points for clarity when listing multiple items
4. Include relevant dollar amounts and percentages when available
5. Be concise but thorough
6. Highlight red flags or important trends
7. Don't provide investment advice (disclaim if necessary)

When analyzing:
- Look for revenue growth trends
- Check profitability margins (gross, operating, net)
- Examine balance sheet strength (debt/equity ratios)
- Review cash flow health
- Identify key risks from risk factors section
- Summarize business overview if relevant

Format responses with clear sections and bullet points when appropriate."""

    def __init__(
        self,
        llm: LLMProvider,
        memory: ConversationMemory,
        tools: Optional[List["Tool"]] = None,
    ) -> None:
        """Initialize the financial agent.

        Args:
            llm: LLM provider for generating responses
            memory: Conversation memory manager
            tools: Optional list of tools the agent can use
        """
        self.llm = llm
        self.memory = memory
        self.tools = {tool.name: tool for tool in (tools or [])}
        logger.info(
            "FinChat initialized",
            extra={"tools": list(self.tools.keys()), "model": llm.model},
        )

    def run(self, user_input: str) -> str:
        """Process user input and generate response.

        Args:
            user_input: User's question or message

        Returns:
            Generated response from the LLM

        Raises:
            Exception: If LLM call fails
        """
        messages = self._build_messages(user_input)
        response = self.llm.chat(messages)
        self.memory.add_message("user", user_input)
        self.memory.add_message("assistant", response)
        return response

    def load_document(self, text: str, source: str) -> str:
        """Load a document into context.

        Args:
            text: Document content
            source: Source name for metadata

        Returns:
            Success message with character count

        Raises:
            DocumentError: If document loading fails
        """
        if not text:
            from ..models import DocumentError
            raise DocumentError("Cannot load empty document")

        try:
            # Truncate if too long
            max_size = self.llm.client.settings.max_document_size
            if len(text) > max_size:
                logger.warning(
                    "Document truncated",
                    extra={
                        "original_length": len(text),
                        "truncated_length": max_size,
                    },
                )
                text = text[:max_size] + "..."

            self.memory.set_document(text, source)
            doc_meta = self.memory.get_document_metadata()
            logger.info(
                "Document loaded successfully",
                extra={
                    "source": source,
                    "character_count": len(text),
                    "truncated": len(text) < len(text),
                },
            )

            if doc_meta:
                return f"Loaded {source} successfully. Document contains {len(text):,} characters. You can now ask questions about it."
            return f"Loaded {source} successfully"

        except Exception as e:
            logger.error("Document loading failed", exc_info=True)
            from ..models import DocumentError
            raise DocumentError(f"Failed to load document: {e}") from e

    def clear_document(self) -> str:
        """Clear document context and history.

        Returns:
            Confirmation message
        """
        self.memory.clear_document()
        return "Document cleared"

    def is_ready(self) -> bool:
        """Check if agent is ready.

        Agent is ready when LLM is available and a document is loaded.

        Returns:
            True if ready, False otherwise
        """
        return self.llm.is_available() and self.memory.has_document()

    def get_document_metadata(self) -> Optional[DocumentMetadata]:
        """Get metadata for the loaded document.

        Returns:
            DocumentMetadata if document loaded, None otherwise
        """
        return self.memory.get_document_metadata()

    def has_document(self) -> bool:
        """Check if a document is loaded.

        Returns:
            True if a document is loaded, False otherwise
        """
        return self.memory.has_document()

    def chat(self, message: str) -> str:
        """Send a message and get a response (alias for run).

        Args:
            message: User's question/message

        Returns:
            Assistant's response text
        """
        return self.run(message)

    def search_document(self, query: str) -> SearchResult:
        """Search for terms in the loaded document.

        Args:
            query: Search query string

        Returns:
            SearchResult with matches

        Raises:
            DocumentError: If no document is loaded
        """
        if "search_document" in self.tools:
            result = self.tools["search_document"].execute(query=query)
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Search failed")
            return result.data
        if len(self.tools) == 1:
            result = next(iter(self.tools.values())).execute(query=query)
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Search failed")
            return result.data
        else:
            # Fallback implementation if tool not provided
            if not self.memory.has_document():
                from ..models import DocumentError
                raise DocumentError("No document loaded")
            extractor = FinDataExtractor()
            matches = extractor.extract_numbers_with_context(
                self.memory.get_document_context(), query
            )
            return SearchResult(
                query=query,
                matches=matches,
                total_matches=len(matches),
                displayed_matches=min(len(matches), 5),
            )

    def analyze_financials(self) -> str:
        """Generate a financial analysis of the loaded document.

        Returns:
            Analysis text

        Raises:
            DocumentError: If no document is loaded
        """
        if not self.memory.has_document():
            from ..models import DocumentError
            raise DocumentError("No document loaded. Please load a financial statement first.")

        if "analyze_financials" in self.tools:
            result = self.tools["analyze_financials"].execute(
                document_context=self.memory.get_document_context()
            )
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Analysis failed")
            return result.data
        if len(self.tools) == 1:
            result = next(iter(self.tools.values())).execute(
                document_context=self.memory.get_document_context()
            )
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Analysis failed")
            return result.data
        else:
            # Fallback: use LLM directly with analysis prompt
            analysis_prompt = """Please provide a concise financial analysis summary including:
1. Key revenue figures and trends
2. Profitability metrics (net income, margins)
3. Balance sheet highlights (total assets, liabilities)
4. Cash flow status
5. Notable risk factors
6. Overall financial health assessment

Format as bullet points with specific numbers where available."""
            # Build messages with analysis_prompt as user message
            # We can call run() but that would add to history? We want to add to history as user+assistant. But we could call run directly.
            # However, run() adds user and assistant to memory. That's fine.
            # But we might want to use a separate method that doesn't add to history? The old analyze_financials called chat internally, which added to history. So we'll do the same.
            return self.run(analysis_prompt)

    def _build_messages(self, user_message: str) -> List[dict[str, str]]:
        """Build complete message list for the LLM API.

        Args:
            user_message: Current user message

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add document context if available
        if self.memory.get_document_context():
            doc_msg = {
                "role": "system",
                "content": f"Document Context:\n\n{self.memory.get_document_context()}\n\nUse this document to answer user questions.",
            }
            messages.append(doc_msg)

        # Add conversation history
        history = self.memory.get_history(limit=CONVERSATION_HISTORY_MAX_EXCHANGES)
        if not isinstance(history, list):
            history = []
        for msg in history:
            messages.append(msg.to_dict())

        # Add current user message as user role
        messages.append({"role": "user", "content": user_message})
        return messages
