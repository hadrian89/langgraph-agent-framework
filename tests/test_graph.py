"""Tests for graph construction and end-to-end execution with mocked LLM."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.agent_registry import AgentRegistry
from app.core.tools_registry import ToolRegistry


@pytest.fixture(autouse=True)
def clean_registries():
    """Isolate registry state for each test."""
    orig_agents = dict(AgentRegistry._agents)
    orig_meta = dict(AgentRegistry._metadata)
    orig_agent_tools = dict(AgentRegistry._agent_tools)
    orig_tools = dict(ToolRegistry._tools)
    yield
    AgentRegistry._agents = orig_agents
    AgentRegistry._metadata = orig_meta
    AgentRegistry._agent_tools = orig_agent_tools
    ToolRegistry._tools = orig_tools


def _register_minimal_agents():
    """Register two lightweight agents sufficient for graph construction tests."""

    def agent_a(state):
        return {"messages": [AIMessage(content="response from agent_a")]}

    def agent_b(state):
        return {"messages": [AIMessage(content="response from agent_b")]}

    AgentRegistry.register("agent_a", agent_a, "Handles type-A requests", tools=[])
    AgentRegistry.register("agent_b", agent_b, "Handles type-B requests", tools=[])


class TestGraphBuild:
    def test_graph_builds_without_error(self):
        _register_minimal_agents()
        from app.core.graph_builder import build_graph

        graph = build_graph("fastapi")
        assert graph is not None

    def test_graph_raises_with_no_agents(self):
        from app.core.graph_builder import build_graph

        with pytest.raises(RuntimeError, match="No agents registered"):
            build_graph("fastapi")

    def test_graph_nodes_include_router_and_tools(self):
        _register_minimal_agents()
        from app.core.graph_builder import build_graph

        graph = build_graph("fastapi")
        node_names = set(graph.get_graph().nodes.keys())
        assert "router" in node_names
        assert "tools" in node_names
        assert "agent_a" in node_names
        assert "agent_b" in node_names


class TestGraphExecution:
    def test_end_to_end_with_mocked_llm(self):
        """Graph should route, invoke agent, and return a response."""
        _register_minimal_agents()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"agent": "agent_a"}'
        mock_llm.invoke.return_value = mock_response

        with patch("app.core.router.LLMGateway.get_model", return_value=mock_llm):
            from app.core.graph_builder import build_graph

            graph = build_graph("fastapi")
            config = {"configurable": {"thread_id": "test-session-1"}}
            result = graph.invoke(
                {"messages": [HumanMessage(content="hello")]},
                config=config,
            )

        assert "messages" in result
        last_msg = result["messages"][-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "response from agent_a"

    def test_session_memory_persists_across_turns(self):
        """Second invocation with the same session_id should see previous messages."""
        _register_minimal_agents()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"agent": "agent_a"}'
        mock_llm.invoke.return_value = mock_response

        with patch("app.core.router.LLMGateway.get_model", return_value=mock_llm):
            from app.core.graph_builder import build_graph

            graph = build_graph("fastapi")
            config = {"configurable": {"thread_id": "test-session-memory"}}

            graph.invoke({"messages": [HumanMessage(content="first message")]}, config=config)
            result = graph.invoke(
                {"messages": [HumanMessage(content="second message")]}, config=config
            )

        # The accumulated messages list should contain both turns
        contents = [m.content for m in result["messages"] if hasattr(m, "content")]
        assert "first message" in contents
        assert "second message" in contents
