from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.state import AgentState
from app.core.agent_registry import AgentRegistry
from app.core.tools_registry import ToolRegistry
from app.core.router import route


def should_continue(state: AgentState):

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return END


def build_graph():

    graph = StateGraph(AgentState)

    tools = ToolRegistry.get_tools()

    graph.add_node("search", AgentRegistry.get_agent("search"))
    graph.add_node("coding", AgentRegistry.get_agent("coding"))

    tool_node = ToolNode(tools)

    graph.add_node("tools", tool_node)

    graph.set_conditional_entry_point(
        route,
        {
            "search": "search",
            "coding": "coding",
        }
    )

    graph.add_conditional_edges(
        "search",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )

    graph.add_edge("tools", "search")

    graph.add_edge("coding", END)

    return graph.compile()