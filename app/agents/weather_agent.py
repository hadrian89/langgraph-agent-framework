from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tracing import trace_node

llm = LLMGateway.get_model()


@trace_node("weather_agent")
def weather_agent(state):

    response = llm.invoke(state["messages"])

    return {"messages": [response]}


AgentRegistry.register("weather", weather_agent)