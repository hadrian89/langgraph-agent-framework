from langchain_core.messages import AIMessage

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.repositories.health_repository import get_recent_health_metrics
from app.services.health.trend_analyzer import analyze_trends


def health_insight_agent(state):

    user_id = state.get("user_id")

    if not user_id:
        return {
            "messages": state["messages"]
            + [AIMessage(content="No user health data available yet.")]
        }
    metrics = get_recent_health_metrics(user_id)

    trends = analyze_trends(metrics)

    llm = LLMGateway.get_model()

    prompt = f"""
You are a health assistant.

User wearable trends:

{trends}

Give a short helpful health suggestion.
Do not diagnose disease.
"""

    response = llm.invoke(prompt)

    return {"messages": state["messages"] + [AIMessage(content=response.content)]}


AgentRegistry.register(
    "health_assistant.insight_agent",
    health_insight_agent,
    "Analyze wearable health trends and give suggestions",
)
