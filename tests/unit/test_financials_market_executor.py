"""Tests for financials tool, market tool, and tool executor."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from finchat_backend.agent_service.tools.financials import FinancialStatementsTool
from finchat_backend.agent_service.tools.market import MarketDataTool
from finchat_backend.agent_service.tools.executor import ToolExecutor
from finchat_backend.agent_service.tools.tool_registry import ToolRegistry
from finchat_backend.agent_service.tools.data_sources.base import DataSourceResult


class TestFinancialStatementsTool:
    """Test FinancialStatementsTool."""

    def test_init_with_default_data_source(self):
        """Test initialization creates YahooFinanceAdapter by default."""
        with patch("finchat_backend.agent_service.tools.financials.YahooFinanceAdapter") as mock_adapter:
            tool = FinancialStatementsTool()
            assert tool.data_source is not None
            mock_adapter.assert_called_once()

    def test_init_with_custom_data_source(self):
        """Test initialization with custom data source."""
        custom_ds = Mock()
        tool = FinancialStatementsTool(data_source=custom_ds)
        assert tool.data_source is custom_ds

    def test_init_without_yfinance_raises(self):
        """Test that missing yfinance raises ImportError."""
        with patch("finchat_backend.agent_service.tools.financials.YahooFinanceAdapter", side_effect=ImportError):
            with pytest.raises(ImportError, match="yfinance"):
                FinancialStatementsTool()

    def test_name_and_description(self):
        """Test tool name and description."""
        tool = FinancialStatementsTool()
        assert tool.name == "get_financial_statements"
        assert "financial statements" in tool.description.lower()

    def test_execute_validates_empty_symbol(self):
        """Test execute rejects empty symbol."""
        tool = FinancialStatementsTool()
        result = tool.execute(symbol="")
        assert result.success is False
        assert "symbol" in result.error.lower()

    def test_execute_validates_invalid_symbol_type(self):
        """Test execute rejects non-string symbol."""
        tool = FinancialStatementsTool()
        result = tool.execute(symbol=123)
        assert result.success is False

    def test_execute_validates_statement_type(self):
        """Test execute validates statement_type parameter."""
        tool = FinancialStatementsTool()
        result = tool.execute(symbol="AAPL", statement_type="invalid")
        assert result.success is False
        assert "statement_type" in result.error.lower()

    def test_execute_validates_period(self):
        """Test execute validates period parameter."""
        tool = FinancialStatementsTool()
        result = tool.execute(symbol="AAPL", period="invalid")
        assert result.success is False
        assert "period" in result.error.lower()

    def test_execute_success_with_all_data(self):
        """Test successful execution retrieving all financial data."""
        tool = FinancialStatementsTool()

        # Mock the data source
        mock_ds = Mock()
        mock_ds.get_financials.return_value = DataSourceResult(
            success=True,
            data={
                "income_statement": [{"date": "2023", "revenue": 100}],
                "balance_sheet": [{"date": "2023", "assets": 200}],
                "cash_flow": [{"date": "2023", "operating": 50}]
            }
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", statement_type="all", period="annual")

        assert result.success is True
        assert "income_statement" in result.data
        assert "balance_sheet" in result.data
        assert "cash_flow" in result.data

    def test_execute_filters_income_statement(self):
        """Test execution filters for income statement only."""
        tool = FinancialStatementsTool()

        mock_ds = Mock()
        mock_ds.get_financials.return_value = DataSourceResult(
            success=True,
            data={
                "income_statement": [{"revenue": 100}],
                "balance_sheet": [{"assets": 200}],
                "cash_flow": [{"operating": 50}]
            }
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="MSFT", statement_type="income")

        assert result.success is True
        assert "income_statement" in result.data
        assert "balance_sheet" not in result.data
        assert "cash_flow" not in result.data

    def test_execute_filters_balance_sheet(self):
        """Test execution filters for balance sheet only."""
        tool = FinancialStatementsTool()

        mock_ds = Mock()
        mock_ds.get_financials.return_value = DataSourceResult(
            success=True,
            data={
                "income_statement": [{"revenue": 100}],
                "balance_sheet": [{"assets": 200}],
                "cash_flow": [{"operating": 50}]
            }
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="GOOGL", statement_type="balance")

        assert result.success is True
        assert "balance_sheet" in result.data
        assert "income_statement" not in result.data
        assert "cash_flow" not in result.data

    def test_execute_handles_data_source_failure(self):
        """Test execution handles data source failure gracefully."""
        tool = FinancialStatementsTool()

        mock_ds = Mock()
        mock_ds.get_financials.return_value = DataSourceResult(
            success=False,
            error="Network error"
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL")

        assert result.success is False
        assert "Network error" in result.error

    def test_execute_handles_exception(self):
        """Test execution handles unexpected exceptions."""
        tool = FinancialStatementsTool()

        mock_ds = Mock()
        mock_ds.get_financials.side_effect = Exception("Unexpected error")
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL")

        assert result.success is False
        assert "Failed to retrieve" in result.error


class TestMarketDataTool:
    """Test MarketDataTool."""

    def test_init_with_default_data_source(self):
        """Test initialization creates YahooFinanceAdapter by default."""
        with patch("finchat_backend.agent_service.tools.market.YahooFinanceAdapter") as mock_adapter:
            tool = MarketDataTool()
            assert tool.data_source is not None
            mock_adapter.assert_called_once()

    def test_init_with_custom_data_source(self):
        """Test initialization with custom data source."""
        custom_ds = Mock()
        tool = MarketDataTool(data_source=custom_ds)
        assert tool.data_source is custom_ds

    def test_name_and_description(self):
        """Test tool name and description."""
        tool = MarketDataTool()
        assert tool.name == "get_market_data"
        assert "market data" in tool.description.lower()

    def test_execute_validates_empty_symbol(self):
        """Test execute rejects empty symbol."""
        tool = MarketDataTool()
        result = tool.execute(symbol="")
        assert result.success is False
        assert "symbol" in result.error.lower()

    def test_execute_validates_data_type(self):
        """Test execute validates data_type parameter."""
        tool = MarketDataTool()
        result = tool.execute(symbol="AAPL", data_type="invalid")
        assert result.success is False
        assert "data_type" in result.error.lower()

    def test_execute_quote_only(self):
        """Test execution with quote data type."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_stock_price.return_value = DataSourceResult(
            success=True,
            data={"symbol": "AAPL", "price": 150.0, "change": 2.5}
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="quote")

        assert result.success is True
        assert "quote" in result.data
        assert result.data["quote"]["price"] == 150.0

    def test_execute_info_only(self):
        """Test execution with info data type."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_company_info.return_value = DataSourceResult(
            success=True,
            data={"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"}
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="info")

        assert result.success is True
        assert "info" in result.data
        assert result.data["info"]["name"] == "Apple Inc."

    def test_execute_historical_only(self):
        """Test execution with historical data type."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_historical_data.return_value = DataSourceResult(
            success=True,
            data=[{"date": "2023-01-01", "close": 150.0}],
            metadata={"period": "1mo", "interval": "1d"}
        )
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="historical", period="1mo", interval="1d")

        assert result.success is True
        assert "historical" in result.data
        assert len(result.data["historical"]) > 0

    def test_execute_all_data_types(self):
        """Test execution with all data types."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_stock_price.return_value = DataSourceResult(success=True, data={"price": 150})
        mock_ds.get_company_info.return_value = DataSourceResult(success=True, data={"name": "Apple"})
        mock_ds.get_historical_data.return_value = DataSourceResult(success=True, data=[{"date": "2023"}])
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="all")

        assert result.success is True
        assert "quote" in result.data
        assert "info" in result.data
        assert "historical" in result.data

    def test_execute_handles_partial_failure(self):
        """Test execution handles partial failures gracefully."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_stock_price.return_value = DataSourceResult(success=True, data={"price": 150})
        mock_ds.get_company_info.return_value = DataSourceResult(success=False, error="Not found")
        mock_ds.get_historical_data.return_value = DataSourceResult(success=True, data=[{"date": "2023"}])
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="all")

        # Should succeed but with missing info
        assert result.success is True
        assert "quote" in result.data
        assert "historical" in result.data
        assert "info" not in result.data

    def test_execute_all_data_sources_fail(self):
        """Test execution fails when all data sources fail."""
        tool = MarketDataTool()

        mock_ds = Mock()
        mock_ds.get_stock_price.return_value = DataSourceResult(success=False, error="API down")
        mock_ds.get_company_info.return_value = DataSourceResult(success=False, error="Not found")
        mock_ds.get_historical_data.return_value = DataSourceResult(success=False, error="Timeout")
        tool.data_source = mock_ds

        result = tool.execute(symbol="AAPL", data_type="all")

        assert result.success is False
        assert "Failed to retrieve any market data" in result.error


class TestToolExecutor:
    """Test ToolExecutor."""

    def test_init_with_registry(self):
        """Test initialization with registry."""
        registry = ToolRegistry()
        executor = ToolExecutor(registry)
        assert executor.registry is registry

    def test_execute_tool_success(self):
        """Test successful tool execution."""
        registry = ToolRegistry()

        def sample_tool(param1: str, param2: int = 10) -> dict:
            return {"param1": param1, "param2": param2, "result": "success"}

        registry.register(
            name="sample_tool",
            func=sample_tool,
            description="Sample tool",
            tool_type="test"
        )

        executor = ToolExecutor(registry)
        result = executor.execute("sample_tool", param1="test", param2=20)

        assert result.success is True
        assert result.data == {"param1": "test", "param2": 20, "result": "success"}

    def test_execute_tool_not_found(self):
        """Test execution of non-existent tool."""
        registry = ToolRegistry()
        executor = ToolExecutor(registry)

        result = executor.execute("nonexistent_tool")

        assert result.success is False
        assert "not found in registry" in result.error

    def test_execute_with_kwargs(self):
        """Test execution using kwargs."""
        registry = ToolRegistry()

        def add(a: int, b: int) -> int:
            return a + b

        registry.register(name="add", func=add)

        executor = ToolExecutor(registry)
        result = executor.execute("add", a=5, b=3)

        assert result.success is True
        assert result.data == 8

    def test_execute_with_params_dict(self):
        """Test execution using params dict."""
        registry = ToolRegistry()

        def multiply(a: int, b: int) -> int:
            return a * b

        registry.register(name="multiply", func=multiply)

        executor = ToolExecutor(registry)
        result = executor.execute("multiply", params={"a": 4, "b": 5})

        assert result.success is True
        assert result.data == 20

    def test_execute_merges_params_and_kwargs(self):
        """Test that kwargs override params dict."""
        registry = ToolRegistry()

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        registry.register(name="greet", func=greet)

        executor = ToolExecutor(registry)
        result = executor.execute(
            "greet",
            params={"name": "World", "greeting": "Hi"},
            greeting="Hello"  # Override
        )

        assert result.success is True
        assert result.data == "Hello, World!"

    def test_execute_wraps_non_toolresult(self):
        """Test that non-ToolResult returns are wrapped."""
        registry = ToolRegistry()

        def plain_func():
            return "plain result"

        registry.register(name="plain", func=plain_func)

        executor = ToolExecutor(registry)
        result = executor.execute("plain")

        assert result.success is True
        assert result.data == "plain result"

    def test_execute_handles_tool_exception(self):
        """Test that tool exceptions are caught and returned as error."""
        registry = ToolRegistry()

        def failing_tool():
            raise ValueError("Something went wrong")

        registry.register(name="failing", func=failing_tool)

        executor = ToolExecutor(registry)
        result = executor.execute("failing")

        assert result.success is False
        assert "Something went wrong" in result.error

    def test_execute_safe_returns_dict(self):
        """Test execute_safe returns dict with standardized keys."""
        registry = ToolRegistry()

        def success_tool():
            return "success"

        registry.register(name="success", func=success_tool)

        executor = ToolExecutor(registry)
        result = executor.execute_safe("success")

        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is True
        assert result["data"] == "success"

    def test_list_available_tools(self):
        """Test listing available tools."""
        registry = ToolRegistry()
        registry.register(name="tool1", func=lambda: 1)
        registry.register(name="tool2", func=lambda: 2)

        executor = ToolExecutor(registry)
        tools = executor.list_available_tools()

        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_get_tool_info(self):
        """Test getting tool information."""
        registry = ToolRegistry()
        registry.register(
            name="my_tool",
            func=lambda: None,
            description="My test tool",
            tool_type="testing",
            metadata={"version": "1.0"}
        )

        executor = ToolExecutor(registry)
        info = executor.get_tool_info("my_tool")

        assert info is not None
        assert info["name"] == "my_tool"
        assert info["description"] == "My test tool"
        assert info["tool_type"] == "testing"
        assert info["metadata"]["version"] == "1.0"

    def test_get_tool_info_not_found(self):
        """Test get_tool_info returns None for missing tool."""
        registry = ToolRegistry()
        executor = ToolExecutor(registry)

        info = executor.get_tool_info("nonexistent")
        assert info is None
