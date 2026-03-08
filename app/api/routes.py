import anyio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.core.agent_loader import load_agents
from app.core.graph_builder import build_graph
from app.core.guardrails import validate_input, validate_output
from app.core.tool_loader import load_tools

router = APIRouter()

load_tools()
load_agents()


graph = build_graph("")


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
    if not validate_input(query):
        return {"response": "Your request violates safety policies."}
    return StreamingResponse(stream_agent(query), media_type="text/event-stream")


@router.post("/chat")
async def chat(query: str):
    if not validate_input(query):
        return {"response": "Your request violates safety policies."}
    with anyio.fail_after(30):
        result = graph.invoke({"messages": [HumanMessage(content=query)]})
        print(f"Graph result: {result}")

    response = result["messages"][-1].content
    if not validate_output(response):
        response = "Response blocked due to safety policy."
    return {"response": response}
