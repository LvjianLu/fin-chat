"""Tool execution engine for running registered tools.

This module provides the ToolExecutor class which serves as the unified
interface for executing tools from the registry.
"""

import logging
from typing import Any, Dict, Optional

from .base import ToolResult
from .tool_registry import ToolRegistry, RegisteredTool

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Unified tool execution engine.

    The ToolExecutor provides a clean interface for executing tools from the
    registry, handling validation, error handling, and result formatting.

    Example:
        from finchat_backend.agent_service.tools import registry, ToolExecutor

        executor = ToolExecutor(registry)

        # Execute a tool by name
        result = executor.execute("get_stock_price", symbol="AAPL")

        # Check result
        if result.success:
            print(result.data)
        else:
            print(f"Error: {result.error}")
    """

    def __init__(self, registry: ToolRegistry):
        """Initialize tool executor.

        Args:
            registry: ToolRegistry instance containing registered tools
        """
        self.registry = registry
        logger.info("ToolExecutor initialized")

    def execute(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        """Execute a tool by name with parameters.

        Args:
            tool_name: Name of the registered tool to execute
            params: Dictionary of parameters to pass to the tool
            **kwargs: Alternative way to pass parameters as keyword arguments

        Returns:
            ToolResult with execution result or error
        """
        try:
            # Get tool from registry
            registered_tool = self.registry.get(tool_name)
            if not registered_tool:
                error_msg = f"Tool '{tool_name}' not found in registry"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg
                )

            # Prepare parameters
            if params is None:
                params = {}
            # Merge kwargs into params (kwargs take precedence)
            merged_params = {**params, **kwargs}

            # Log execution attempt
            logger.info(
                f"Executing tool: {tool_name}",
                extra={"tool": tool_name, "param_count": len(merged_params)}
            )

            # Execute the tool
            tool_func = registered_tool.func
            result = tool_func(**merged_params)

            # Ensure result is a ToolResult
            if not isinstance(result, ToolResult):
                logger.warning(
                    f"Tool '{tool_name}' returned non-ToolResult, wrapping automatically",
                    extra={"tool": tool_name, "result_type": type(result).__name__}
                )
                result = ToolResult(success=True, data=result)

            return result

        except Exception as e:
            logger.error(
                f"Tool '{tool_name}' execution failed",
                exc_info=True
            )
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    def execute_safe(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a tool and return a standardized dictionary result.

        This is a convenience method that returns a dict with 'success', 'data', and 'error' keys.

        Args:
            tool_name: Name of the registered tool to execute
            params: Dictionary of parameters
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary with keys: success (bool), data (any), error (str or None)
        """
        result = self.execute(tool_name, params, **kwargs)
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

    def list_available_tools(self) -> Dict[str, RegisteredTool]:
        """Get all available tools from the registry.

        Returns:
            Dictionary mapping tool names to RegisteredTool objects
        """
        return self.registry.list_tools()

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary with tool metadata, or None if not found
        """
        registered_tool = self.registry.get(tool_name)
        if not registered_tool:
            return None

        return {
            "name": registered_tool.name,
            "description": registered_tool.description,
            "tool_type": registered_tool.tool_type,
            "metadata": registered_tool.metadata,
        }
