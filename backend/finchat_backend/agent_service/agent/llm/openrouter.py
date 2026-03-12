"""OpenRouter LLM provider implementation.

Wraps the OpenRouterClient to provide a clean LLMProvider interface.
"""

import logging
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ...config import Settings
from ...constants import DEFAULT_TEMPERATURE, MAX_TOKENS_PER_RESPONSE
from ...models import APIError, ConfigurationError
from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Internal OpenRouter API client (moved from integrations)."""

    def __init__(self, settings: Settings) -> None:
        """Initialize OpenRouter client.

        Args:
            settings: Application settings with API credentials

        Raises:
            ConfigurationError: If API key is missing
        """
        self.settings = settings
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.openrouter_model
        self.temperature = DEFAULT_TEMPERATURE
        self.max_tokens = MAX_TOKENS_PER_RESPONSE

        if not self.api_key:
            raise ConfigurationError("OpenRouter API key is required")

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.info(
                "OpenRouter client initialized",
                extra={"model": self.model, "base_url": self.base_url},
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize OpenRouter client: {e}") from e

    def build_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[list] = None,
        document_context: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Build complete message list for API call.

        Args:
            system_prompt: System prompt defining behavior
            user_message: Current user message
            conversation_history: Previous conversation messages (list of ChatMessage or dicts)
            document_context: Optional document context to include

        Returns:
            List of message dictionaries ready for API
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if document_context:
            doc_message = (
                f"Document Context:\n\n{document_context}\n\n"
                "Use this document to answer user questions."
            )
            messages.append({"role": "system", "content": doc_message})

        if conversation_history:
            for msg in conversation_history:
                if hasattr(msg, "to_dict"):
                    messages.append(msg.to_dict())
                else:
                    messages.append(msg)

        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send chat completion request.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's response text

        Raises:
            APIError: If API call fails
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            logger.info(
                "Making OpenRouter API call",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "temperature": temp,
                    "max_tokens": tokens,
                },
            )

            response: ChatCompletion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )

            assistant_message = response.choices[0].message.content
            if not assistant_message:
                raise APIError("Empty response from API")

            usage = getattr(response, "usage", None)
            if usage:
                logger.info(
                    "API call completed",
                    extra={
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    },
                )

            return assistant_message

        except Exception as e:
            logger.error("OpenRouter API call failed", exc_info=True)
            raise APIError(f"OpenRouter API error: {e}") from e

    def is_available(self) -> bool:
        """Check if client is properly initialized and available."""
        return self.client is not None


class OpenRouterLLM(LLMProvider):
    """OpenRouter LLM provider implementation.

    This wraps the OpenRouterClient to conform to the LLMProvider interface.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize OpenRouter LLM provider.

        Args:
            settings: Application settings

        Raises:
            ConfigurationError: If initialization fails
        """
        self.client = OpenRouterClient(settings)
        self._model = settings.openrouter_model
        self._temperature = DEFAULT_TEMPERATURE
        self._max_tokens = MAX_TOKENS_PER_RESPONSE
        logger.info(
            "OpenRouterLLM initialized",
            extra={"model": self._model},
        )

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Send messages to OpenRouter and get response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Optional overrides (temperature, max_tokens)

        Returns:
            Response text from the LLM
        """
        return self.client.chat(messages, **kwargs)

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self.client.is_available())

    @property
    def model(self) -> str:
        """Return the model identifier."""
        return self._model
