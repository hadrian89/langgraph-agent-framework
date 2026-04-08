from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.logging import logger
from app.core.tools_registry import ToolRegistry
from app.core.tracing import trace_node

_TOOLS = ["search"]


@trace_node("search_agent")
def search_agent(state: dict) -> dict:
    llm = LLMGateway.get_model()
    tools = ToolRegistry.get_tools_by_names(_TOOLS)
    llm_with_tools = llm.bind_tools(tools)

    logger.info("search_agent invoked")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


AgentRegistry.register(
    name="search",
    agent_fn=search_agent,
    description="Answers factual questions, world knowledge, and real-time web searches",
    tools=_TOOLS,
)
