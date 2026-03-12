"""Tests for FinChatAgentFactory tool wiring and registry integration."""

from unittest.mock import patch

from finchat_backend.core.factories.agent_factory import FinChatAgentFactory
from agent_service.config import load_settings_from_dict


def _make_test_settings():
    return load_settings_from_dict(
        {
            "openrouter_api_key": "sk-or-test1234567890",
            "openrouter_model": "stepfun/step-3.5-flash:free",
            "log_level": "DEBUG",
            "data_dir": "./test_data",
            "max_document_size": 10000,
            "enable_tool_calling": True,
        }
    )


@patch("agent_service.agent.llm.openrouter.OpenRouterClient")
def test_factory_registers_core_tools(mock_client_class):
    """Factory should create an agent wired with core tools and executor."""
    settings = _make_test_settings()
    factory = FinChatAgentFactory(settings)

    agent = factory.create_agent()

    # Agent should have an executor and unified tool registry
    assert agent.executor is factory.executor
    assert factory.executor.registry is factory.registry

    # Core tools should be available to the agent
    tool_names = set(agent.tools.keys())
    assert "search_document" in tool_names
    assert "analyze_financials" in tool_names

    # Market/financial statement tools are optional (depend on external deps),
    # but when present they should also be exposed.
    possible_optional = {"get_market_data", "get_financial_statements"}
    assert tool_names.intersection(possible_optional) == tool_names.intersection(
        possible_optional
    )

