"""Tool registration system for managing and discovering tools.

This module provides a centralized registry for tools that can be used by agents.
It allows for dynamic registration, discovery, and execution of tools.
"""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RegisteredTool:
    """Metadata about a registered tool.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description
        func: The callable to execute the tool
        tool_type: Category/type of the tool (e.g., "datasource", "analysis", "search")
        metadata: Additional metadata about the tool
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        tool_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.tool_type = tool_type
        self.metadata = metadata or {}


class ToolRegistry:
    """Central registry for managing tools.

    The ToolRegistry provides a unified interface for:
    - Registering tools (functions or classes)
    - Discovering available tools
    - Executing tools by name
    - Grouping tools by category

    Example:
        registry = ToolRegistry()

        # Register a tool
        def my_tool(param1: str) -> dict:
            return {"result": param1}

        registry.register(
            name="my_tool",
            func=my_tool,
            description="My custom tool",
            tool_type="general"
        )

        # Execute a tool
        result = registry.execute("my_tool", param1="value")
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, RegisteredTool] = {}
        logger.info("ToolRegistry initialized")

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        tool_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register a tool in the registry.

        Args:
            name: Unique identifier for the tool
            func: The callable to execute when the tool is invoked
            description: Human-readable description of what the tool does
            tool_type: Category/type of the tool (e.g., "datasource", "analysis")
            metadata: Additional metadata about the tool

        Returns:
            True if registration succeeded

        Raises:
            ValueError: If name is empty or func is not callable
        """
        if not name:
            raise ValueError("Tool name cannot be empty")

        if not callable(func):
            raise ValueError(f"Tool '{name}' func must be callable")

        if name in self._tools:
            logger.warning(f"Tool '{name}' is already registered. Overwriting.")

        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            func=func,
            tool_type=tool_type,
            metadata=metadata or {},
        )

        logger.info(
            f"Tool registered: {name}",
            extra={"tool_name": name, "tool_type": tool_type}
        )
        return True

    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            name: Name of the tool to remove

        Returns:
            True if tool was removed, False if tool not found
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Tool unregistered: {name}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent tool: {name}")
            return False

    def get(self, name: str) -> Optional[RegisteredTool]:
        """Get a registered tool by name.

        Args:
            name: Name of the tool to retrieve

        Returns:
            RegisteredTool object if found, None otherwise
        """
        return self._tools.get(name)

    def get_callable(self, name: str) -> Optional[Callable]:
        """Get the callable function for a registered tool.

        Args:
            name: Name of the tool

        Returns:
            Callable if tool exists, None otherwise
        """
        tool = self._tools.get(name)
        return tool.func if tool else None

    def list_tools(self, tool_type: Optional[str] = None) -> Dict[str, RegisteredTool]:
        """List all registered tools, optionally filtered by type.

        Args:
            tool_type: If provided, only return tools of this type

        Returns:
            Dictionary mapping tool names to RegisteredTool objects
        """
        if tool_type is None:
            return self._tools.copy()

        return {
            name: tool
            for name, tool in self._tools.items()
            if tool.tool_type == tool_type
        }

    def get_tool_types(self) -> Dict[str, int]:
        """Get counts of tools by type.

        Returns:
            Dictionary mapping tool types to counts
        """
        type_counts: Dict[str, int] = {}
        for tool in self._tools.values():
            type_counts[tool.tool_type] = type_counts.get(tool.tool_type, 0) + 1
        return type_counts

    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()
        logger.info("Tool registry cleared")

    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool name is in the registry."""
        return name in self._tools

    def __iter__(self):
        """Iterate over registered tool names."""
        return iter(self._tools.values())

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a registered tool by name.

        Args:
            name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool function

        Returns:
            The result returned by the tool function

        Raises:
            KeyError: If the tool is not registered
            RuntimeError: If tool execution fails
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")

        try:
            result = tool.func(**kwargs)
            return result
        except Exception as e:
            logger.error(
                f"Tool '{name}' execution failed",
                exc_info=True
            )
            raise RuntimeError(f"Tool execution failed: {e}") from e


# Global default registry instance for convenience
registry = ToolRegistry()
