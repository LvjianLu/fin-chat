"""Tests for tool calling fallback behavior when model doesn't support tools."""

import json
import pytest
from unittest.mock import Mock, patch

from agent_service.agent.agent import FinChat
from agent_service.agent.llm.openrouter import OpenRouterLLM
from agent_service.agent.memory import ConversationMemory
from agent_service.tools import MarketDataTool
from agent_service.config import Settings, load_settings_from_dict


class TestToolCallingFallback:
    """Test fallback behavior when tools fail."""

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_fallback_when_model_doesnt_support_tools(self, mock_client_class, test_settings):
        """Test that agent falls back to simple chat when tool call fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # First call with tools raises an error (model doesn't support tools)
        mock_client.chat.side_effect = [
            Exception("Model does not support tool calls"),  # Tool call fails
            "I can help you with financial questions!"  # Fallback succeeds
        ]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        market_tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[market_tool], enable_tool_calling=True)

        result = agent.run("Hello!")

        # Should have fallen back to simple chat and returned the second response
        assert result == "I can help you with financial questions!"
        # Should have called LLM twice (first failed tool attempt, then fallback)
        assert mock_client.chat.call_count == 2

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_tool_calling_disabled(self, mock_client_class, test_settings):
        """Test that agent uses simple chat when tool calling is disabled."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = "Simple chat response"

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        market_tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[market_tool], enable_tool_calling=False)

        result = agent.run("Query stock price")

        # Should only call LLM once (no tool attempt)
        assert result == "Simple chat response"
        assert mock_client.chat.call_count == 1
        # Verify that tools parameter was not passed
        call_kwargs = mock_client.chat.call_args[1]
        assert 'tools' not in call_kwargs

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_fallback_preserves_conversation(self, mock_client_class, test_settings):
        """Test that fallback still saves conversation to memory."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = [
            Exception("Tool call not supported"),
            "I'm here to help!"
        ]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        market_tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[market_tool], enable_tool_calling=True)

        result = agent.run("Test message")

        assert result == "I'm here to help!"
        history = memory.get_history()
        assert len(history) == 2
        assert history[0].content == "Test message"
        assert history[1].content == "I'm here to help!"
