from typing import Callable, List, Optional


class AgentRegistry:
    """
    Central registry for all agents.

    Agents declare their name, handler function, a human-readable description
    (used by the LLM router to pick the right agent), and optionally the list
    of tool names they are allowed to use.

    Example
    -------
    AgentRegistry.register(
        name="search",
        agent_fn=search_agent,
        description="Answers factual questions using web search",
        tools=["search"],
    )
    """

    _agents: dict[str, Callable] = {}
    _metadata: dict[str, str] = {}
    _agent_tools: dict[str, List[str]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        agent_fn: Callable,
        description: str = "",
        tools: Optional[List[str]] = None,
    ) -> None:
        cls._agents[name] = agent_fn
        cls._metadata[name] = description
        cls._agent_tools[name] = tools or []

    @classmethod
    def get_agent(cls, name: str) -> Callable:
        if name not in cls._agents:
            raise KeyError(f"Agent '{name}' is not registered.")
        return cls._agents[name]

    @classmethod
    def get_agent_tools(cls, name: str) -> List[str]:
        """Return the list of tool names declared by this agent."""
        return cls._agent_tools.get(name, [])

    @classmethod
    def list_agents(cls) -> List[str]:
        return list(cls._agents.keys())

    @classmethod
    def all_agents(cls) -> dict[str, Callable]:
        return cls._agents

    @classmethod
    def get_metadata(cls) -> dict[str, str]:
        return cls._metadata
