import anyio
from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from app.core.agent_loader import load_agents
from app.core.tool_loader import load_tools

from app.core.graph_builder import build_graph

router = APIRouter()

load_tools()
load_agents()


graph = build_graph()


@router.post("/chat")
async def chat(query: str):
    with anyio.fail_after(30):
        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]}
        )
        print(f"Graph result: {result}")

    return {
        "response": result["messages"][-1].content
    }