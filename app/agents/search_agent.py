from app.core.tracing import trace_node
from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry
from app.core.logging import logger

llm = LLMGateway.get_model()
tools = ToolRegistry.get_tools()

llm_with_tools = llm.bind_tools(tools)


@trace_node("search_agent")
def search_agent(state):
    logger.info("search_agent invoked")
    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


AgentRegistry.register("search", search_agent,"Answers factual questions, world knowledge, and current information")