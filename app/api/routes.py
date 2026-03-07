import anyio
from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from app.core.agent_loader import load_agents
from app.core.tool_loader import load_tools
from fastapi.responses import StreamingResponse

from app.core.graph_builder import build_graph

router = APIRouter()

load_tools()
load_agents()


graph = build_graph()

def stream_agent(query: str):

    inputs = {"messages": [HumanMessage(content=query)]}

    for event in graph.stream(inputs):

        for value in event.values():

            if "messages" in value:

                message = value["messages"][-1]

                if hasattr(message, "content") and message.content:

                    yield f"data: {message.content}\n\n"
                    
                    
@router.get("/chat/stream")
async def chat_stream(query: str):

    return StreamingResponse(
        stream_agent(query),
        media_type="text/event-stream"
    )
    
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