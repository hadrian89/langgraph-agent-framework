from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph_checkpoint_aws import AgentCoreMemorySaver

from app.core.agent_registry import AgentRegistry
from app.core.router import route
from app.core.tools_registry import ToolRegistry
from app.state import AgentState

REGION = "eu-west-2"
MEMORY_ID = "agentframework_mem-0kn5PJ2mTf"
MODEL_ID = "gpt-4o-mini"


def should_continue(state):

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return END


def build_graph(endpoint_type):
    if endpoint_type == "agentcore":
        checkpointer = AgentCoreMemorySaver(MEMORY_ID, region_name=REGION)

    graph = StateGraph(AgentState)

    tools = ToolRegistry.get_tools()

    # add tool node
    tool_node = ToolNode(tools)
    graph.add_node("tools", tool_node)

    # dynamically register all agents
    agents = AgentRegistry.all_agents()
    print("Agents in graph:", AgentRegistry.list_agents())
    print("Graph agents:", agents.keys())
    for name, agent in agents.items():

        graph.add_node(name, agent)

        graph.add_conditional_edges(
            name,
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )

    # tool loop back to agent
    for name in agents.keys():
        graph.add_edge("tools", name)

    graph.set_conditional_entry_point(route, {name: name for name in agents.keys()})
    if endpoint_type == "agentcore":
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()
