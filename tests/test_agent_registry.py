"""Tests for AgentRegistry."""

import pytest

from app.core.agent_registry import AgentRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry state before each test to prevent cross-test pollution."""
    original_agents = dict(AgentRegistry._agents)
    original_metadata = dict(AgentRegistry._metadata)
    original_tools = dict(AgentRegistry._agent_tools)
    yield
    AgentRegistry._agents = original_agents
    AgentRegistry._metadata = original_metadata
    AgentRegistry._agent_tools = original_tools


def _dummy_agent(state):
    return {"messages": []}


class TestRegister:
    def test_register_basic(self):
        AgentRegistry.register("test", _dummy_agent, "A test agent")
        assert "test" in AgentRegistry.list_agents()

    def test_register_stores_description(self):
        AgentRegistry.register("test", _dummy_agent, "My description")
        assert AgentRegistry.get_metadata()["test"] == "My description"

    def test_register_stores_tools(self):
        AgentRegistry.register("test", _dummy_agent, "desc", tools=["search", "weather"])
        assert AgentRegistry.get_agent_tools("test") == ["search", "weather"]

    def test_register_defaults_to_empty_tools(self):
        AgentRegistry.register("test", _dummy_agent, "desc")
        assert AgentRegistry.get_agent_tools("test") == []

    def test_register_overwrites_existing(self):
        AgentRegistry.register("test", _dummy_agent, "first")
        AgentRegistry.register("test", _dummy_agent, "second")
        assert AgentRegistry.get_metadata()["test"] == "second"


class TestGetAgent:
    def test_get_registered_agent(self):
        AgentRegistry.register("test", _dummy_agent)
        assert AgentRegistry.get_agent("test") is _dummy_agent

    def test_get_unknown_agent_raises(self):
        with pytest.raises(KeyError, match="not registered"):
            AgentRegistry.get_agent("does_not_exist")


class TestListAgents:
    def test_list_returns_registered_names(self):
        AgentRegistry.register("alpha", _dummy_agent)
        AgentRegistry.register("beta", _dummy_agent)
        agents = AgentRegistry.list_agents()
        assert "alpha" in agents
        assert "beta" in agents

    def test_all_agents_returns_dict(self):
        AgentRegistry.register("test", _dummy_agent)
        all_agents = AgentRegistry.all_agents()
        assert isinstance(all_agents, dict)
        assert "test" in all_agents
