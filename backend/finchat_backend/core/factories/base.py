"""Factory abstractions for backend runtime creation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from finchat_backend.core.bootstrap import ensure_project_path

ensure_project_path()

from agent_service.agent.agent import FinChat
from finchat_backend.core.models import MessagePayload


class AgentFactory(ABC):
    """Build configured FinChat agents."""

    @abstractmethod
    def create_agent(
        self,
        messages: Optional[list[MessagePayload]] = None,
        document_context: Optional[str] = None,
        doc_source: Optional[str] = None,
    ) -> FinChat:
        """Create a configured FinChat runtime."""
