from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from state import AgentState
from tools import tools
from agents import planner_agent, executor_agent, supervisor_agent
from evaluator import evaluate_response

tool_node = ToolNode(tools)


def should_use_tool(state):

    last = state["messages"][-1]

    if last.tool_calls:
        return "tools"

    return "evaluate"


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_agent)
    graph.add_node("executor", executor_agent)
    graph.add_node("tools", tool_node)
    graph.add_node("evaluate", evaluate_response)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "executor")

    graph.add_conditional_edges(
        "executor",
        should_use_tool,
        {
            "tools": "tools",
            "evaluate": "evaluate",
        },
    )

    graph.add_edge("tools", "executor")

    graph.add_edge("evaluate", END)

    return graph.compile()