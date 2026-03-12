"""End-to-end test for real-world stock query scenario."""

import json
import pytest
from unittest.mock import Mock, patch

from agent_service.agent.agent import FinChat
from agent_service.agent.llm.openrouter import OpenRouterLLM
from agent_service.agent.memory import ConversationMemory
from agent_service.tools import MarketDataTool
from agent_service.config import Settings, load_settings_from_dict


class TestE2EStockQuery:
    """End-to-end tests for stock price queries."""

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_query_alibaba_stock_price(self, mock_client_class, test_settings):
        """Test: User asks for Alibaba's previous day closing price.

        This is the exact scenario from the user's feedback.
        The agent should automatically use get_market_data tool.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # First response: agent decides to use market data tool
        first_response = {
            "content": "I'll retrieve the current market data for Alibaba (BABA).",
            "tool_calls": [
                {
                    "id": "call_market_1",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": json.dumps({
                            "symbol": "BABA",
                            "data_type": "quote"
                        })
                    }
                }
            ]
        }

        # Second response: agent provides final answer
        final_response = "阿里巴巴(BABA)昨日收盘价为$85.50，涨幅+1.2%。"

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        market_tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[market_tool])

        # Execute the query
        result = agent.run("查询阿里巴巴昨日美股的收盘价")

        # Verify the response
        assert "85.50" in result or "85.5" in result
        assert "阿里巴巴" in result or "BABA" in result

        # Verify that two LLM calls were made (initial + after tool)
        assert mock_client.chat.call_count == 2

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_query_apple_financials(self, mock_client_class, test_settings):
        """Test: User asks for Apple's financial statements."""
        from agent_service.tools import FinancialStatementsTool

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = {
            "content": "Let me fetch Apple's financial statements.",
            "tool_calls": [
                {
                    "id": "call_fin_1",
                    "type": "function",
                    "function": {
                        "name": "get_financial_statements",
                        "arguments": json.dumps({
                            "symbol": "AAPL",
                            "statement_type": "income",
                            "period": "annual"
                        })
                    }
                }
            ]
        }

        final_response = "Apple's latest annual revenue is $394.3B with net income of $99.8B."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()
        fin_tool = FinancialStatementsTool()
        agent = FinChat(llm=llm, memory=memory, tools=[fin_tool])

        result = agent.run("What is Apple's annual revenue?")

        assert "394.3B" in result or "394.3" in result
        assert mock_client.chat.call_count == 2

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_query_without_document_uses_market_tool(self, mock_client_class, test_settings):
        """Test that agent can use market data tool even without a document."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        first_response = {
            "content": "Checking market data...",
            "tool_calls": [
                {
                    "id": "call_mkt_1",
                    "type": "function",
                    "function": {
                        "name": "get_market_data",
                        "arguments": json.dumps({
                            "symbol": "MSFT",
                            "data_type": "quote"
                        })
                    }
                }
            ]
        }

        final_response = "Microsoft (MSFT) is currently trading at $300.25."

        mock_client.chat.side_effect = [first_response, final_response]

        llm = OpenRouterLLM(test_settings)
        memory = ConversationMemory()  # No document loaded
        market_tool = MarketDataTool()
        agent = FinChat(llm=llm, memory=memory, tools=[market_tool])

        result = agent.run("What's Microsoft's stock price?")

        assert "300.25" in result
        assert mock_client.chat.call_count == 2
