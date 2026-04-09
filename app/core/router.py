import json

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.logging import logger
from app.core.tracing import trace_node

_FALLBACK_AGENT = "search"

_ROUTER_PROMPT = """You are an intelligent routing engine for a multi-agent AI platform.

Your only job is to decide which agent should handle the user request.

Available agents:
{agent_descriptions}

Rules:
- Choose the single most relevant agent.
- Return ONLY a JSON object — no explanation, no markdown.
- Format: {{"agent": "<agent_name>"}}

User request:
{query}
"""


@trace_node("router")
def router_node(state: dict) -> dict:
    """
    LangGraph node that selects the best agent for the current request.

    Returns a state update containing `active_agent` — the name of the agent
    that should handle this turn. Conditional edges in the graph use this value
    to route execution.
    """
    llm = LLMGateway.get_model()
    query = state["messages"][-1].content
    agents = AgentRegistry.get_metadata()

    agent_descriptions = "\n".join([f"  {name}: {desc}" for name, desc in agents.items()])

    prompt = _ROUTER_PROMPT.format(
        agent_descriptions=agent_descriptions,
        query=query,
    )

    response = llm.invoke(prompt)

    # Handle both string and list content (Bedrock vs OpenAI)
    raw = response.content
    if isinstance(raw, list):
        raw = "".join(str(item) for item in raw)
    raw = raw.strip()

    try:
        agent = json.loads(raw)["agent"]
    except Exception:
        logger.warning(
            "Router failed to parse LLM output: %r — falling back to '%s'", raw, _FALLBACK_AGENT
        )
        agent = _FALLBACK_AGENT

    if agent not in agents:
        logger.warning(
            "Router returned unknown agent '%s' — falling back to '%s'", agent, _FALLBACK_AGENT
        )
        agent = _FALLBACK_AGENT

    logger.info("Router selected agent: %s", agent)
    return {"active_agent": agent}


def get_next_agent(state: dict) -> str:
    """
    Conditional-edge function: returns the name of the currently active agent.
    Used both after the router node and after the tool node.
    """
    return state.get("active_agent", _FALLBACK_AGENT)
