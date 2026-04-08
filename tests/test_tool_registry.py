"""Tests for ToolRegistry."""

import pytest

from app.core.tools_registry import ToolRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry state before each test."""
    original = dict(ToolRegistry._tools)
    yield
    ToolRegistry._tools = original


def _dummy_tool(query: str) -> str:
    """A dummy tool for testing."""
    return f"result: {query}"


def _another_tool(location: str) -> str:
    """Another dummy tool."""
    return f"weather: {location}"


class TestRegister:
    def test_register_and_list(self):
        ToolRegistry.register("dummy", _dummy_tool)
        assert "dummy" in ToolRegistry.list_tools()

    def test_register_multiple(self):
        ToolRegistry.register("tool_a", _dummy_tool)
        ToolRegistry.register("tool_b", _another_tool)
        tools = ToolRegistry.list_tools()
        assert "tool_a" in tools
        assert "tool_b" in tools


class TestGetTool:
    def test_get_registered_tool(self):
        ToolRegistry.register("dummy", _dummy_tool)
        assert ToolRegistry.get_tool("dummy") is _dummy_tool

    def test_get_unknown_tool_raises(self):
        with pytest.raises(KeyError, match="not registered"):
            ToolRegistry.get_tool("does_not_exist")


class TestGetTools:
    def test_get_tools_returns_list(self):
        ToolRegistry.register("dummy", _dummy_tool)
        tools = ToolRegistry.get_tools()
        assert isinstance(tools, list)
        assert _dummy_tool in tools


class TestGetToolsByNames:
    def test_returns_only_requested_tools(self):
        ToolRegistry.register("search", _dummy_tool)
        ToolRegistry.register("weather", _another_tool)
        result = ToolRegistry.get_tools_by_names(["search"])
        assert result == [_dummy_tool]
        assert _another_tool not in result

    def test_returns_multiple_tools_in_order(self):
        ToolRegistry.register("a", _dummy_tool)
        ToolRegistry.register("b", _another_tool)
        result = ToolRegistry.get_tools_by_names(["b", "a"])
        assert result == [_another_tool, _dummy_tool]

    def test_raises_for_missing_tool(self):
        ToolRegistry.register("search", _dummy_tool)
        with pytest.raises(KeyError, match="not registered"):
            ToolRegistry.get_tools_by_names(["search", "missing"])

    def test_empty_list_returns_empty(self):
        result = ToolRegistry.get_tools_by_names([])
        assert result == []
