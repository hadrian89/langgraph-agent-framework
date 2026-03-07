from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.state import AgentState
from app.core.agent_registry import AgentRegistry
from app.core.tools_registry import ToolRegistry
from app.core.router import route

from app.core.tracing import trace_node
from langgraph.prebuilt import ToolNode


class TracedToolNode(ToolNode):

    @trace_node("tool_execution")
    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)

def should_continue(state):
    #print("STATE MESSAGES:", state["messages"])
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return END


def build_graph():

    graph = StateGraph(AgentState)

    tools = ToolRegistry.get_tools()

    search_agent = AgentRegistry.get_agent("search")
    coding_agent = AgentRegistry.get_agent("coding")

    graph.add_node("search", search_agent)
    graph.add_node("coding", coding_agent)

    tool_node = TracedToolNode(tools)
    graph.add_node("tools", tool_node)

    # dynamic entry point
    graph.set_conditional_entry_point(
        route,
        {
            "search": "search",
            "coding": "coding",
        }
    )

    # ReAct loop
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