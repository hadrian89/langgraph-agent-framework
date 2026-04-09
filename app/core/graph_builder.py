from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.core.agent_registry import AgentRegistry
from app.core.logging import logger
from app.core.router import get_next_agent, router_node
from app.core.tools_registry import ToolRegistry
from app.state.agent_state import AgentState

# AWS Bedrock AgentCore settings (used only when endpoint_type="agentcore")
_AGENTCORE_REGION = "eu-west-2"
_AGENTCORE_MEMORY_ID = "agentframework_mem-0kn5PJ2mTf"


def _should_continue(state: dict) -> str:
    """After an agent runs, decide whether to call tools or finish."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph(endpoint_type: str = "fastapi"):
    """
    Build and compile the LangGraph StateGraph.

    Parameters
    ----------
    endpoint_type : str
        "fastapi"   — in-process MemorySaver (session memory within a server run)
        "agentcore" — AWS Bedrock AgentCoreMemorySaver (persistent cross-session memory)

    Graph structure
    ---------------
    [entry] → router_node → <agent> → (tool_calls?) → tools → <same agent> → …→ END
    """
    agents = AgentRegistry.all_agents()
    if not agents:
        raise RuntimeError("No agents registered. Call load_agents() before build_graph().")

    all_tools = ToolRegistry.get_tools()
    agent_names = list(agents.keys())

    # -- Checkpointer ---------------------------------------------------------
    if endpoint_type == "agentcore":
        try:
            from langgraph_checkpoint_aws import AgentCoreMemorySaver

            checkpointer = AgentCoreMemorySaver(_AGENTCORE_MEMORY_ID, region_name=_AGENTCORE_REGION)
            logger.info("Graph using AgentCoreMemorySaver (region=%s)", _AGENTCORE_REGION)
        except ImportError as exc:
            raise ImportError(
                "langgraph-checkpoint-aws is required for AgentCore deployment. "
                "Run: uv add langgraph-checkpoint-aws"
            ) from exc
    else:
        checkpointer = MemorySaver()
        logger.info("Graph using in-process MemorySaver")

    # -- Build graph ----------------------------------------------------------
    graph = StateGraph(AgentState)

    # Router node: decides which agent handles the request and sets active_agent
    graph.add_node("router", router_node)
    graph.set_entry_point("router")

    # Shared tool execution node — holds ALL registered tools
    tool_node = ToolNode(all_tools)
    graph.add_node("tools", tool_node)

    # One node per registered agent
    for name, agent_fn in agents.items():
        graph.add_node(name, agent_fn)
        # After an agent runs: call tools if needed, else finish
        graph.add_conditional_edges(name, _should_continue, {"tools": "tools", END: END})

    # After router: route to the agent it selected
    agent_routing = {name: name for name in agent_names}
    graph.add_conditional_edges("router", get_next_agent, agent_routing)

    # After tools: route back to the SAME agent that initiated the tool call
    # (get_next_agent reads active_agent from state — set by the router node)
    graph.add_conditional_edges("tools", get_next_agent, agent_routing)

    logger.info("Graph built with agents: %s", agent_names)
    logger.info("Graph built with tools: %s", ToolRegistry.list_tools())

    return graph.compile(checkpointer=checkpointer)
