"""Base classes for tool implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


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
    """Abstract base class for all tools."""

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
