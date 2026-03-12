"""Concrete FinChat agent factory."""

from __future__ import annotations

from typing import Optional, List
import logging
from importlib import import_module

from finchat_backend.core.bootstrap import ensure_project_path

ensure_project_path()

from agent_service.config import Settings
from finchat_backend.core.factories.base import AgentFactory
from finchat_backend.core.models import MessagePayload


logger = logging.getLogger(__name__)


class FinChatAgentFactory(AgentFactory):
    """Create fully wired FinChat runtimes for backend sessions."""

    def __init__(self, settings: Settings):
        self.settings = settings

        # Initialize the unified tool registry and executor
        from finchat_backend.agent_service.tools import registry, ToolExecutor
        self.registry = registry
        self.executor = ToolExecutor(registry)

    def create_agent(
        self,
        messages: Optional[list[MessagePayload]] = None,
        document_context: Optional[str] = None,
        doc_source: Optional[str] = None,
    ):
        """Build a FinChat agent with shared backend defaults."""
        from agent_service.agent.agent import FinChat
        from agent_service.agent.llm.openrouter import OpenRouterLLM
        from agent_service.agent.memory import ConversationMemory
        from agent_service.tools import (
            FinAnalysisTool,
            SearchTool,
        )

        llm = OpenRouterLLM(self.settings)
        memory = ConversationMemory()

        if document_context and doc_source:
            # Truncate document to max_document_size to avoid exceeding LLM context limits
            max_size = self.settings.max_document_size
            if len(document_context) > max_size:
                document_context = document_context[:max_size] + "..."
            memory.set_document(document_context, doc_source)

        for message in messages or []:
            memory.add_message(message["role"], message["content"])

        # Base tools that require runtime dependencies (LLM, memory)
        tools: List = [
            SearchTool(memory),
            FinAnalysisTool(llm),
        ]

        # Discover additional tools from the shared registry using their metadata,
        # instead of hard-coding concrete tool classes here.
        for name, registered in self.registry.list_tools().items():
            metadata = getattr(registered, "metadata", {}) or {}

            # Only attach generic "data" tools (e.g. market data, financial statements)
            if getattr(registered, "tool_type", None) != "data":
                continue

            module_name = metadata.get("module")
            class_name = metadata.get("class")
            if not module_name or not class_name:
                continue

            try:
                module = import_module(module_name)
                tool_cls = getattr(module, class_name)
                instance = tool_cls()
            except Exception as exc:
                logger.warning(
                    "Failed to instantiate tool from registry entry",
                    extra={
                        "tool_name": name,
                        "module": module_name,
                        "class": class_name,
                        "error": str(exc),
                    },
                )
                continue

            # Avoid duplicates by tool name
            if any(getattr(t, "name", None) == getattr(instance, "name", None) for t in tools):
                continue

            tools.append(instance)

        return FinChat(
            tools=tools,
            llm=llm,
            memory=memory,
            executor=self.executor,
            enable_tool_calling=self.settings.enable_tool_calling,
        )
