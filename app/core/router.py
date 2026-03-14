import json

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tracing import trace_node


@trace_node("router")
def route(state):
    llm = LLMGateway.get_model()

    query = state["messages"][-1].content

    query_lower = query.lower()

    if "trend" in query_lower or "health report" in query_lower:
        return "health_assistant.insight_agent"

    if "sleep" in query_lower or "tired" in query_lower:
        return "health_assistant.sleep_agent"

    if "exercise" in query_lower or "steps" in query_lower:
        return "health_assistant.activity_agent"

    if "diet" in query_lower or "food" in query_lower:
        return "health_assistant.nutrition_agent"

    agents = AgentRegistry.get_metadata()

    agent_descriptions = "\n".join([f"{name}: {desc}" for name, desc in agents.items()])

    prompt = f"""
You are an intelligent router for a multi-agent AI system.

Your task is to choose the BEST agent to handle the user request.

Available agents:

{agent_descriptions}

Instructions:
- Select the most relevant agent
- Only return JSON
- Do not explain
- Format: {{"agent": "agent_name"}}

User request:
{query}
"""

    response = llm.invoke(prompt)

    if isinstance(response.content, list):
        text = "".join(str(item) for item in response.content).strip()
    else:
        text = response.content.strip()
    print("Router raw output:", text)
    try:
        agent = json.loads(text)["agent"]
    except Exception:
        agent = "health_assistant.conversation"

    if agent not in agents:
        agent = "health_assistant.conversation"

    print(f"Routed to agent: {agent}")

    return agent
