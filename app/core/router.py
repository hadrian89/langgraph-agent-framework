import json

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tracing import trace_node


@trace_node("router")
def route(state):
    llm = LLMGateway.get_model()

    query = state["messages"][-1].content

    agents = AgentRegistry.get_metadata()

    agent_descriptions = "\n".join([f"{name}: {desc}" for name, desc in agents.items()])

    prompt = f"""
You are a routing engine for an AI agent platform.

Agents and capabilities:

{agent_descriptions}

Rules:
- Choose the best agent for the request
- Return JSON ONLY
- Do not explain

Example:
{{"agent": "search"}}

User request:
{query}
"""

    response = llm.invoke(prompt)

    text = response.content.strip()

    try:

        agent = json.loads(text)["agent"]
    except Exception:
        agent = "search"

    if agent not in agents:
        agent = "search"

    print(f"Routed to agent: {agent}")

    return agent
