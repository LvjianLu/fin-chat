"""Tests for agent tool calling functionality (ReAct pattern)."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from agent_service.agent.agent import FinChat
from agent_service.agent.llm.openrouter import OpenRouterLLM
from agent_service.agent.memory import ConversationMemory
from agent_service.tools import SearchTool, FinAnalysisTool, MarketDataTool, FinancialStatementsTool, ToolResult
from agent_service.config import Settings, load_settings_from_dict


class TestFinChatToolCalling:
    """Test FinChat's tool calling capabilities."""

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_tool_call(self, mock_client_class, test_settings):
        """Test that agent can call tools when LLM requests it."""
        # Setup mock LLM
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # First call returns a response with tool calls
        first_response = {
            "content": "I'll look up that stock price for you.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": json.dumps({"symbol": "BABA", "data_type": "quote"})
                    }
                }
            ]
        }
        # Second call returns final answer
        final_response = "阿里巴巴(BABA)昨日收盘价为$85.50。"

        mock_client.chat.side_effect = [first_response, final_response]

        # Setup agent with MarketDataTool
        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[tool])

        # Run agent
        result = agent.run("查询阿里巴巴昨日美股的收盘价")

        # Verify result
        assert result == "阿里巴巴(BABA)昨日收盘价为$85.50。"

        # Verify LLM was called twice (initial + after tool execution)
        assert mock_client.chat.call_count == 2

        # Verify memory was updated
        history = memory.get_history()
        assert len(history) == 2
        assert history[0].content == "查询阿里巴巴昨日美股的收盘价"
        assert history[1].content == "阿里巴巴(BABA)昨日收盘价为$85.50。"

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_multiple_tool_calls(self, mock_client_class, test_settings):
        """Test that agent can handle multiple tool calls in one turn."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # First call requests two tools
        first_response = {
            "content": "Let me fetch the data.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": json.dumps({"symbol": "AAPL", "data_type": "quote"})
                    }
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "get_financial_statements",
                        "arguments": json.dumps({"symbol": "AAPL", "statement_type": "income"})
                    }
                }
            ]
        }
        final_response = "Apple's current stock price is $150 with revenue of $100B."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        agent = FinChat(
            llm=llm,
            memory=memory,
            tools=[MarketDataTool(), FinancialStatementsTool()]
        )

        result = agent.run("告诉我苹果公司的股价和收入")

        assert result == "Apple's current stock price is $150 with revenue of $100B."
        assert mock_client.chat.call_count == 2

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_without_tool_call(self, mock_client_class, test_settings):
        """Test that normal chat works when no tool call is made."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # LLM returns plain text, no tool calls
        mock_client.chat.return_value = "I can help you with financial analysis!"

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        tool = MarketDataTool()  # Have a tool available but not used
        agent = FinChat(llm=llm, memory=memory, tools=[tool])

        result = agent.run("Hello!")

        assert result == "I can help you with financial analysis!"
        # Should only call LLM once (no tool execution)
        assert mock_client.chat.call_count == 1

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_search_tool(self, mock_client_class, test_settings):
        """Test agent using search_document tool."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = {
            "content": "I'll search the document for you.",
            "tool_calls": [
                {
                    "id": "call_search",
                    "type": "function",
                    "function": {
                        "name": "search_document",
                        "arguments": json.dumps({"query": "revenue"})
                    }
                }
            ]
        }
        final_response = "The document contains information about revenue: $100 million."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        memory.set_document("Revenue was $100 million.", "Test Doc")
        search_tool = SearchTool(memory)
        agent = FinChat(llm=llm, memory=memory, tools=[search_tool])

        result = agent.run("Find revenue in the document")

        assert result == "The document contains information about revenue: $100 million."
        assert mock_client.chat.call_count == 2

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_handles_tool_error(self, mock_client_class, test_settings):
        """Test that agent handles tool execution errors gracefully."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = {
            "content": "Checking...",
            "tool_calls": [
                {
                    "id": "call_err",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": json.dumps({"symbol": "INVALID", "data_type": "quote"})
                    }
                }
            ]
        }
        final_response = "I apologize, but I couldn't retrieve the market data due to an error."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        # Mock tool to fail
        tool = Mock()
        tool.name = "get_market_data"
        tool.execute.return_value = ToolResult(success=False, error="Symbol not found")
        agent = FinChat(llm=llm, memory=memory, tools=[tool])

        result = agent.run("Get data for INVALID")

        # Should still produce a response
        assert result == "I apologize, but I couldn't retrieve the market data due to an error."

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_invalid_tool_args(self, mock_client_class, test_settings):
        """Test that agent handles invalid JSON arguments gracefully."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Invalid JSON arguments
        first_response = {
            "content": "Let me check...",
            "tool_calls": [
                {
                    "id": "call_bad_json",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": "invalid json {{{{"
                    }
                }
            ]
        }
        final_response = "I apologize, there was an issue with the request."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[tool])

        result = agent.run("Get stock price")

        assert result == "I apologize, there was an issue with the request."

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_unknown_tool(self, mock_client_class, test_settings):
        """Test that agent handles unknown tool names gracefully."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = {
            "content": "Trying...",
            "tool_calls": [
                {
                    "id": "call_unknown",
                    "type": "function",
                    "function": {
                        "name": "unknown_tool",
                        "arguments": json.dumps({})
                    }
                }
            ]
        }
        final_response = "I don't have access to that specific tool."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[tool])

        result = agent.run("Do something")

        assert result == "I don't have access to that specific tool."

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_run_with_xml_style_tool_call(self, mock_client_class, test_settings):
        """Test that XML-style tool call markup is executed and summarized."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = (
            "我来帮您查询阿里巴巴（BABA）昨日美股的收盘价。"
            "<tool_call>"
            "<function=get_market_data>"
            "<parameter=symbol>BABA</parameter>"
            "<parameter=data_type>quote</parameter>"
            "</function>"
            "</tool_call>"
        )
        final_response = "阿里巴巴(BABA)昨日收盘价为$85.50。"
        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        tool = Mock()
        tool.name = "get_market_data"
        tool.to_openai_function.return_value = {
            "type": "function",
            "function": {
                "name": "get_market_data",
                "description": "Retrieve market data",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        tool.execute.return_value = ToolResult(
            success=True,
            data={"quote": {"symbol": "BABA", "previous_close": 85.50, "currency": "USD"}},
        )

        agent = FinChat(llm=llm, memory=memory, tools=[tool])
        result = agent.run("查询阿里巴巴昨日美股的收盘价")

        assert result == final_response
        assert mock_client.chat.call_count == 2
        tool.execute.assert_called_once_with(symbol="BABA", data_type="quote")
