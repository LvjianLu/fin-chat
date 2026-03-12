"""Concrete FinChat agent factory."""

from __future__ import annotations

from typing import Optional

from finchat_backend.core.bootstrap import ensure_project_path

ensure_project_path()

from agent_service.config import Settings
from finchat_backend.core.factories.base import AgentFactory
from finchat_backend.core.models import MessagePayload


class FinChatAgentFactory(AgentFactory):
    """Create fully wired FinChat runtimes for backend sessions."""

    def __init__(self, settings: Settings):
        self.settings = settings

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
        from agent_service.agent.tools import FinAnalysisTool, SearchTool

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

        tools = [
            SearchTool(memory),
            FinAnalysisTool(llm),
        ]
        return FinChat(tools=tools, llm=llm, memory=memory)
