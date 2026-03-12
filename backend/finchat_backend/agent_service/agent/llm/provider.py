"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for language model providers."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Send messages to LLM and return response text.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific arguments (temperature, max_tokens, etc.)

        Returns:
            Response text from the LLM

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is properly initialized and available.

        Returns:
            True if provider is ready to use, False otherwise
        """
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model identifier being used.

        Returns:
            Model name/identifier string
        """
        pass
