from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.logging import logger
from app.core.tools_registry import ToolRegistry
from app.core.tracing import trace_node

_TOOLS = ["weather"]


@trace_node("weather_agent")
def weather_agent(state: dict) -> dict:
    llm = LLMGateway.get_model()
    tools = ToolRegistry.get_tools_by_names(_TOOLS)
    llm_with_tools = llm.bind_tools(tools)

    logger.info("weather_agent invoked")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


AgentRegistry.register(
    name="weather",
    agent_fn=weather_agent,
    description="Handles weather queries — current conditions, temperature, and forecasts for any location",
    tools=_TOOLS,
)
