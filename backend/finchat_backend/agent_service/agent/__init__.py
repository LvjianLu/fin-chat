"""Agent framework for financial chatbot.

This module re-exports core agent components, using the unified tool system
from finchat_backend.agent_service.tools.
"""

# Re-export from unified tools system
from finchat_backend.agent_service.tools import (
    Tool,
    ToolResult,
    SearchTool,
    FinAnalysisTool,
    FinancialStatementsTool,
    MarketDataTool,
    ToolExecutor,
)

# Agent classes
from .agent import Agent, FinChat
from .llm import LLMProvider
from .memory import ConversationMemory

__all__ = [
    # Agent
    "Agent",
    "FinChat",
    # LLM
    "LLMProvider",
    # Memory
    "ConversationMemory",
    # Tools (from unified system)
    "Tool",
    "ToolResult",
    "SearchTool",
    "FinAnalysisTool",
    "FinancialStatementsTool",
    "MarketDataTool",
    # Executor
    "ToolExecutor",
]
