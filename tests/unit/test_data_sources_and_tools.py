"""Tests for data_sources module and tool_registry."""

import pytest
from unittest.mock import Mock, patch

from agent_service.tools.tool_registry import ToolRegistry, RegisteredTool
from agent_service.tools.data_sources.base import DataSourceAdapter, DataSourceResult


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_registry_initialization(self):
        """Test that registry initializes empty."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert list(registry.list_tools()) == []

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()

        def sample_tool(param1: str, param2: int = 10) -> dict:
            return {"param1": param1, "param2": param2}

        registry.register(
            name="sample_tool",
            func=sample_tool,
            description="A sample test tool",
            tool_type="test",
            metadata={"version": "1.0"}
        )

        assert "sample_tool" in registry
        assert len(registry) == 1

        tool = registry.get("sample_tool")
        assert tool is not None
        assert tool.name == "sample_tool"
        assert tool.description == "A sample test tool"
        assert tool.tool_type == "test"
        assert tool.metadata == {"version": "1.0"}
        assert tool.func is sample_tool

    def test_register_duplicate_tool_overwrites(self):
        """Test that registering duplicate tool logs warning but overwrites."""
        registry = ToolRegistry()

        def tool_v1():
            return "v1"

        def tool_v2():
            return "v2"

        registry.register(name="duplicate_tool", func=tool_v1, description="V1")
        # Should overwrite without raising
        registry.register(name="duplicate_tool", func=tool_v2, description="V2")

        assert registry.get("duplicate_tool").func() == "v2"

    def test_register_empty_name_raises(self):
        """Test that empty tool name raises ValueError."""
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            registry.register(name="", func=lambda: None)

    def test_register_non_callable_raises(self):
        """Test that non-callable func raises ValueError."""
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="func must be callable"):
            registry.register(name="not_callable", func="not a function")

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        registry.register(name="to_remove", func=lambda: None)

        assert registry.unregister("to_remove") is True
        assert len(registry) == 0
        assert "to_remove" not in registry

    def test_unregister_nonexistent_returns_false(self):
        """Test unregistering non-existent tool returns False."""
        registry = ToolRegistry()
        assert registry.unregister("nonexistent") is False

    def test_get_callable(self):
        """Test getting callable from registry."""
        registry = ToolRegistry()

        def my_func():
            return "result"

        registry.register(name="my_func", func=my_func)
        assert registry.get_callable("my_func") is my_func
        assert registry.get_callable("nonexistent") is None

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()

        registry.register(name="tool1", func=lambda: 1, tool_type="type1")
        registry.register(name="tool2", func=lambda: 2, tool_type="type2")
        registry.register(name="tool3", func=lambda: 3, tool_type="type1")

        tools = registry.list_tools()
        assert len(tools) == 3
        assert "tool1" in tools
        assert "tool2" in tools
        assert "tool3" in tools

    def test_list_tools_filtered_by_type(self):
        """Test listing tools filtered by type."""
        registry = ToolRegistry()

        registry.register(name="tool1", func=lambda: 1, tool_type="type1")
        registry.register(name="tool2", func=lambda: 2, tool_type="type2")
        registry.register(name="tool3", func=lambda: 3, tool_type="type1")

        type1_tools = registry.list_tools(tool_type="type1")
        assert len(type1_tools) == 2
        assert "tool1" in type1_tools
        assert "tool3" in type1_tools
        assert "tool2" not in type1_tools

    def test_get_tool_types(self):
        """Test getting counts of tools by type."""
        registry = ToolRegistry()

        registry.register(name="t1", func=lambda: 1, tool_type="type1")
        registry.register(name="t2", func=lambda: 2, tool_type="type2")
        registry.register(name="t3", func=lambda: 3, tool_type="type1")
        registry.register(name="t4", func=lambda: 4, tool_type="type1")

        type_counts = registry.get_tool_types()
        assert type_counts == {"type1": 3, "type2": 1}

    def test_execute_tool(self):
        """Test executing a registered tool."""
        registry = ToolRegistry()

        def add(a: int, b: int) -> int:
            return a + b

        registry.register(name="add", func=add, description="Add two numbers")

        result = registry.execute("add", a=5, b=3)
        assert result == 8

    def test_execute_nonexistent_tool_raises(self):
        """Test executing non-existent tool raises KeyError."""
        registry = ToolRegistry()

        with pytest.raises(KeyError, match="not found in registry"):
            registry.execute("nonexistent")

    def test_execute_tool_raises_on_error(self):
        """Test that tool execution errors are wrapped in RuntimeError."""
        registry = ToolRegistry()

        def failing_tool():
            raise ValueError("Tool failed")

        registry.register(name="failing", func=failing_tool)

        with pytest.raises(RuntimeError, match="execution failed"):
            registry.execute("failing")

    def test_contains(self):
        """Test 'in' operator works for tool names."""
        registry = ToolRegistry()
        registry.register(name="exists", func=lambda: None)

        assert "exists" in registry
        assert "not_exists" not in registry

    def test_iteration(self):
        """Test iterating over registry yields RegisteredTool objects."""
        registry = ToolRegistry()
        registry.register(name="t1", func=lambda: 1)
        registry.register(name="t2", func=lambda: 2)

        tools = list(registry)
        assert len(tools) == 2
        assert all(isinstance(t, RegisteredTool) for t in tools)

    def test_clear(self):
        """Test clearing all tools from registry."""
        registry = ToolRegistry()
        registry.register(name="t1", func=lambda: 1)
        registry.register(name="t2", func=lambda: 2)

        registry.clear()
        assert len(registry) == 0
        assert list(registry.list_tools()) == []


class TestDataSourceResult:
    """Test DataSourceResult dataclass."""

    def test_success_result_is_truthy(self):
        """Test that successful result is truthy."""
        result = DataSourceResult(success=True, data={"key": "value"})
        assert result.success is True
        assert bool(result) is True

    def test_failure_result_is_falsy(self):
        """Test that failure result is falsy."""
        result = DataSourceResult(success=False, error="Something went wrong")
        assert result.success is False
        assert bool(result) is False

    def test_result_with_all_fields(self):
        """Test result with all fields populated."""
        metadata = {"source": "test", "count": 10}
        result = DataSourceResult(
            success=True,
            data={"test": "data"},
            error=None,
            metadata=metadata
        )

        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.error is None
        assert result.metadata == metadata


class TestDataSourceAdapter:
    """Test DataSourceAdapter abstract base class."""

    def test_has_required_methods(self):
        """Test that DataSourceAdapter defines required abstract methods."""
        assert hasattr(DataSourceAdapter, 'get_stock_price')
        assert hasattr(DataSourceAdapter, 'get_company_info')
        assert hasattr(DataSourceAdapter, 'get_historical_data')
        assert hasattr(DataSourceAdapter, 'get_historical_data')
        assert hasattr(DataSourceAdapter, 'get_financials')
        assert hasattr(DataSourceAdapter, 'health_check')

    def test_cannot_instantiate_abstract_class(self):
        """Test that DataSourceAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            DataSourceAdapter()


@pytest.mark.integration
class TestYahooFinanceAdapter:
    """Test YahooFinanceAdapter (integration tests)."""

    def test_adapter_initialization(self):
        """Test adapter can be initialized."""
        try:
            from agent_service.tools.data_sources.yahoo_adapter import YahooFinanceAdapter
            adapter = YahooFinanceAdapter()
            assert adapter is not None
        except ImportError as e:
            pytest.skip(f"yfinance not available: {e}")

    def test_health_check(self):
        """Test health check returns OK for AAPL."""
        try:
            from agent_service.tools.data_sources.yahoo_adapter import YahooFinanceAdapter
        except ImportError as e:
            pytest.skip(f"yfinance not available: {e}")

        adapter = YahooFinanceAdapter()
        health = adapter.health_check()

        # Health check should succeed (network dependent)
        # We just check it returns proper structure
        assert isinstance(health, DataSourceResult)
        if health.success:
            assert health.data == "OK"
            assert "source" in health.metadata

    def test_get_stock_price_returns_proper_structure(self):
        """Test get_stock_price returns expected data structure."""
        try:
            from agent_service.tools.data_sources.yahoo_adapter import YahooFinanceAdapter
        except ImportError as e:
            pytest.skip(f"yfinance not available: {e}")

        adapter = YahooFinanceAdapter()
        result = adapter.get_stock_price("AAPL")

        assert isinstance(result, DataSourceResult)
        if result.success:
            assert "price" in result.data
            assert "symbol" in result.data
            assert result.data["symbol"] == "AAPL"

    def test_get_company_info_returns_proper_structure(self):
        """Test get_company_info returns expected data structure."""
        try:
            from agent_service.tools.data_sources.yahoo_adapter import YahooFinanceAdapter
        except ImportError as e:
            pytest.skip(f"yfinance not available: {e}")

        adapter = YahooFinanceAdapter()
        result = adapter.get_company_info("AAPL")

        assert isinstance(result, DataSourceResult)
        if result.success:
            assert "name" in result.data
            assert "sector" in result.data
            assert "industry" in result.data
