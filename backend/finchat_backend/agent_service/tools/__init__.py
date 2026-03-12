"""Unified tools registry and management system.

This package provides:
- Tool base classes and interfaces (Tool, ToolResult)
- Data source adapters for external APIs
- Centralized tool registry for tool discovery
- Tool executor for unified tool execution
"""

import logging
from typing import Dict, Optional

from .tool_registry import ToolRegistry, RegisteredTool, registry as global_registry
from .base import Tool, ToolResult
from .executor import ToolExecutor

# Import data sources
from .data_sources import (
    DataSourceAdapter,
    DataSourceResult,
    YahooFinanceAdapter,
)

# Import tool classes explicitly for export
from .search_tool import SearchTool
from .analysis_tool import FinAnalysisTool
from .financials import FinancialStatementsTool
from .market import MarketDataTool

# Import modules for access to implementations
from . import search_tool
from . import analysis_tool
from . import financials
from . import market

logger = logging.getLogger(__name__)


def auto_discover_and_register(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """Automatically discover all tool classes and register them.

    This function scans the tools package for Tool subclasses and registers
    them with the provided registry (or the global registry by default).

    Args:
        registry: Optional ToolRegistry to use. If None, uses the global registry.

    Returns:
        The registry with all discovered tools registered.
    """
    if registry is None:
        registry = global_registry

    # Map of module -> (tool_class, name_attr, description, type)
    tool_modules = [
        (search_tool, "SearchTool", "search", "document"),
        (analysis_tool, "FinAnalysisTool", "analyze_financials", "analysis"),
        (financials, "FinancialStatementsTool", "get_financial_statements", "data"),
        (market, "MarketDataTool", "get_market_data", "data"),
    ]

    registered_count = 0
    for module, class_name, expected_name, default_type in tool_modules:
        try:
            tool_class = getattr(module, class_name)
            # Create instance to get name and description
            # Handle tools that require constructor args differently
            if class_name == "SearchTool":
                # SearchTool requires memory arg - skip auto-register, user must register manually
                logger.info(f"Skipped auto-registration for {class_name} (requires constructor args)")
                continue
            elif class_name == "FinAnalysisTool":
                # FinAnalysisTool requires llm arg - skip auto-register
                logger.info(f"Skipped auto-registration for {class_name} (requires constructor args)")
                continue
            else:
                # Other tools can be instantiated without args
                tool_instance = tool_class()
                tool_name = tool_instance.name
                description = tool_instance.description

            # Register the tool class (not instance) - we'll instantiate on execution
            # Actually, we need to register an instance or factory. Let's register the class with a wrapper
            def make_tool_func(tool_cls):
                """Create a function that instantiates and executes the tool."""
                def tool_func(**kwargs):
                    # For tools that need dependencies, they should be instantiated externally
                    # and registered. For simple tools, we instantiate here.
                    if tool_cls.__name__ in ["FinancialStatementsTool", "MarketDataTool"]:
                        # These can be instantiated without args
                        instance = tool_cls()
                        return instance.execute(**kwargs)
                    else:
                        raise RuntimeError(f"Tool {tool_cls.__name__} requires manual registration with dependencies")
                return tool_func

            # Register the tool
            registry.register(
                name=tool_name,
                func=make_tool_func(tool_class),
                description=description,
                tool_type=default_type,
                metadata={"module": module.__name__, "class": class_name}
            )
            registered_count += 1
            logger.info(f"Auto-registered tool: {tool_name}")

        except Exception as e:
            logger.error(f"Failed to auto-register tool from {module.__name__}: {e}")

    logger.info(f"Auto-discovery complete: {registered_count} tools registered")
    return registry


# Perform auto-discovery on module import
_initial_registry = auto_discover_and_register(global_registry)

# Expose the global registry for external use
registry = global_registry

__all__ = [
    # Core
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "registry",
    "RegisteredTool",
    "ToolExecutor",
    "auto_discover_and_register",
    # Data Sources
    "DataSourceAdapter",
    "DataSourceResult",
    "YahooFinanceAdapter",
    # Tool implementation classes
    "SearchTool",
    "FinAnalysisTool",
    "FinancialStatementsTool",
    "MarketDataTool",
    # Tool implementation modules (for advanced use)
    "search_tool",
    "analysis_tool",
    "financials",
    "market",
]
