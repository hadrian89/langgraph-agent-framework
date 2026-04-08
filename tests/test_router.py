"""Tests for the router node."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.core.agent_registry import AgentRegistry
from app.core.router import get_next_agent, router_node


@pytest.fixture(autouse=True)
def clean_registry():
    original_agents = dict(AgentRegistry._agents)
    original_metadata = dict(AgentRegistry._metadata)
    original_tools = dict(AgentRegistry._agent_tools)
    AgentRegistry._agents = {"search": lambda s: s, "weather": lambda s: s, "coding": lambda s: s}
    AgentRegistry._metadata = {
        "search": "Answers factual questions via web search",
        "weather": "Handles weather queries for any location",
        "coding": "Writes and debugs code",
    }
    AgentRegistry._agent_tools = {"search": ["search"], "weather": ["weather"], "coding": []}
    yield
    AgentRegistry._agents = original_agents
    AgentRegistry._metadata = original_metadata
    AgentRegistry._agent_tools = original_tools


def _state(query: str) -> dict:
    return {"messages": [HumanMessage(content=query)]}


def _mock_llm_response(text: str):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = text
    mock_llm.invoke.return_value = mock_response
    return mock_llm


class TestRouterNode:
    def test_routes_to_search(self):
        with patch(
            "app.core.router.LLMGateway.get_model",
            return_value=_mock_llm_response('{"agent": "search"}'),
        ):
            result = router_node(_state("Who is the PM of the UK?"))
        assert result == {"active_agent": "search"}

    def test_routes_to_weather(self):
        with patch(
            "app.core.router.LLMGateway.get_model",
            return_value=_mock_llm_response('{"agent": "weather"}'),
        ):
            result = router_node(_state("What is the weather in Tokyo?"))
        assert result == {"active_agent": "weather"}

    def test_routes_to_coding(self):
        with patch(
            "app.core.router.LLMGateway.get_model",
            return_value=_mock_llm_response('{"agent": "coding"}'),
        ):
            result = router_node(_state("Write a binary search in Python"))
        assert result == {"active_agent": "coding"}

    def test_falls_back_on_invalid_json(self):
        with patch(
            "app.core.router.LLMGateway.get_model",
            return_value=_mock_llm_response("not json at all"),
        ):
            result = router_node(_state("some query"))
        assert result == {"active_agent": "search"}

    def test_falls_back_on_unknown_agent(self):
        with patch(
            "app.core.router.LLMGateway.get_model",
            return_value=_mock_llm_response('{"agent": "nonexistent_agent"}'),
        ):
            result = router_node(_state("some query"))
        assert result == {"active_agent": "search"}

    def test_falls_back_on_empty_response(self):
        with patch("app.core.router.LLMGateway.get_model", return_value=_mock_llm_response("")):
            result = router_node(_state("some query"))
        assert result == {"active_agent": "search"}


class TestGetNextAgent:
    def test_returns_active_agent_from_state(self):
        state = {"active_agent": "weather", "messages": []}
        assert get_next_agent(state) == "weather"

    def test_falls_back_when_active_agent_missing(self):
        state = {"messages": []}
        assert get_next_agent(state) == "search"
