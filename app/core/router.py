from app.core.llm_gateway import LLMGateway
from app.core.agent_registry import AgentRegistry
from app.core.tracing import trace_node

llm = LLMGateway.get_model()


@trace_node("router")
def route(state):

    query = state["messages"][-1].content

    agents = AgentRegistry.list_agents()

    prompt = f"""
You are a router for an AI agent system.

Available agents:
{agents}

User query:
{query}

Return ONLY the best agent name.
"""

    response = llm.invoke(prompt)

    agent = response.content.strip()

    if agent not in agents:
        agent = agents[0]

    print(f"Routed to agent: {agent}")

    return agent