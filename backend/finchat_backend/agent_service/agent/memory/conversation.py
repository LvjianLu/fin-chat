"""Conversation memory management."""

import logging
from typing import List, Optional

from ...constants import CONVERSATION_HISTORY_MAX_EXCHANGES
from ...models import ChatMessage, DocumentMetadata

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history and document context.

    This class encapsulates all state related to conversation history
    and the currently loaded document. It provides methods to add
    messages, manage document context, and retrieve history.
    """

    def __init__(self, max_history: int = CONVERSATION_HISTORY_MAX_EXCHANGES):
        """Initialize conversation memory.

        Args:
            max_history: Maximum number of conversation exchanges to keep
                        (each exchange = 1 user + 1 assistant message)
        """
        self.max_history = max_history
        self._messages: List[ChatMessage] = []
        self._document_context: str = ""
        self._document_metadata: Optional[DocumentMetadata] = None

        logger.debug(
            "ConversationMemory initialized", extra={"max_history": max_history}
        )

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        msg = ChatMessage(role=role, content=content)
        self._messages.append(msg)
        self._trim_history()
        logger.debug(
            "Message added",
            extra={"role": role, "history_length": len(self._messages)},
        )

    def get_history(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history.

        Args:
            limit: Optional number of exchanges to return (returns recent history)
                  Note: limit is in exchanges, not individual messages

        Returns:
            List of ChatMessage objects
        """
        if limit is None:
            return self._messages

        # Convert exchanges to messages (2 messages per exchange)
        max_msgs = limit * 2
        return self._messages[-max_msgs:]

    def set_document(self, text: str, source: str) -> None:
        """Load a document into context.

        This clears any existing conversation history and document context.

        Args:
            text: Document text content
            source: Source name/identifier for metadata
        """
        if not text:
            raise ValueError("Cannot set empty document")

        self._document_context = text
        self._document_metadata = DocumentMetadata(
            source_name=source, character_count=len(text)
        )
        self._messages = []  # Clear history on new document
        logger.info(
            "Document loaded",
            extra={"source": source, "character_count": len(text)},
        )

    def clear_document(self) -> None:
        """Remove document context and clear history."""
        self._document_context = ""
        self._document_metadata = None
        self._messages = []
        logger.info("Document and history cleared")

    def get_document_context(self) -> str:
        """Get the current document context.

        Returns:
            Document text content
        """
        return self._document_context

    def get_document_metadata(self) -> Optional[DocumentMetadata]:
        """Get metadata for the loaded document.

        Returns:
            DocumentMetadata if document is loaded, None otherwise
        """
        return self._document_metadata

    def has_document(self) -> bool:
        """Check if a document is loaded.

        Returns:
            True if document context exists, False otherwise
        """
        return bool(self._document_context)

    def _trim_history(self) -> None:
        """Trim conversation history to maximum size."""
        max_msgs = self.max_history * 2
        if len(self._messages) > max_msgs:
            self._messages = self._messages[-max_msgs:]
            logger.debug(
                "Conversation history trimmed",
                extra={"new_length": len(self._messages)},
            )

    def clear_history(self) -> None:
        """Clear conversation history but keep document context."""
        self._messages = []
        logger.debug("Conversation history cleared")

    def to_dict(self) -> dict:
        """Convert memory state to dictionary for serialization.

        Returns:
            Dictionary representation of memory state
        """
        return {
            "messages": [msg.to_dict() for msg in self._messages],
            "document_context": self._document_context,
            "document_metadata": (
                {
                    "source_name": self._document_metadata.source_name,
                    "character_count": self._document_metadata.character_count,
                }
                if self._document_metadata
                else None
            ),
            "max_history": self.max_history,
        }
