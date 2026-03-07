from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry
from app.core.telemetry import tracer

llm = LLMGateway.get_model()

llm_with_tools = llm.bind_tools(ToolRegistry.get_tools())


def search_agent(state):
    with tracer.start_as_current_span("search_agent"):

        messages = state["messages"]

        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}
    #messages = state["messages"]

    #response = llm_with_tools.invoke(messages)

    #return {"messages": [response]}


AgentRegistry.register("search", search_agent)