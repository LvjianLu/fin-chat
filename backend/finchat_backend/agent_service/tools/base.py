"""Base classes for all tools and tool results."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Standardized result from tool execution.

    Attributes:
        success: Whether the tool executed successfully
        data: The result data (can be any type)
        error: Error message if execution failed
    """

    success: bool
    data: Any = None
    error: Optional[str] = None

    def __bool__(self) -> bool:
        """Allow ToolResult to be used in boolean context."""
        return self.success


class Tool(ABC):
    """Abstract base class for all tools.

    Tools encapsulate specific functionality that can be invoked by agents
    or through the ToolExecutor. Each tool must have a unique name and
    description for LLM understanding.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool.

        Returns:
            Tool name (e.g., "search_document", "analyze_financials")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does, for LLM understanding.

        Returns:
            Human-readable description of tool functionality
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and result data
        """
        pass

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for tool parameters for function calling.

        Subclasses should override this to provide precise parameter definitions.
        Default implementation returns a generic schema with no required parameters.

        Returns:
            Dictionary following JSON Schema format
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format.

        Returns:
            Dictionary with 'type': 'function' and nested 'function' object
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }

    def to_function_schema(self) -> Dict[str, Any]:
        """Legacy: convert tool to function schema (without type wrapper).

        Returns:
            Dictionary with 'name', 'description', and 'parameters' keys
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema()
        }

