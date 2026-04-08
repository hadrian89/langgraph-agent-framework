from typing import Any, Optional

import anyio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.core.agent_loader import load_agents
from app.core.graph_builder import build_graph
from app.core.guardrails import validate_input, validate_output
from app.core.session import get_or_create_session
from app.core.tool_loader import load_tools

router = APIRouter()

load_tools()
load_agents()
graph = build_graph("fastapi")


def _make_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _stream_agent(query: str, session_id: str):
    inputs: Any = {"messages": [HumanMessage(content=query)]}
    config = _make_config(session_id)

    for event in graph.stream(inputs, config=config):  # type: ignore[arg-type]
        for value in event.values():
            if "messages" in value:
                message = value["messages"][-1]
                if hasattr(message, "content") and message.content:
                    yield f"data: {message.content}\n\n"


@router.get("/chat/stream")
async def chat_stream(query: str, session_id: Optional[str] = None):
    """
    Stream a response via Server-Sent Events.

    Pass `session_id` to continue an existing conversation thread.
    A new session ID is returned on the first request; pass it on subsequent
    calls to maintain memory.
    """
    if not validate_input(query):
        return {"error": "Your request violates safety policies."}

    session_id = get_or_create_session(session_id)
    return StreamingResponse(
        _stream_agent(query, session_id),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/chat")
async def chat(query: str, session_id: Optional[str] = None):
    """
    Send a message and receive a complete response.

    Pass `session_id` to continue an existing conversation thread.
    The session ID is echoed back in the response so the client can
    use it for the next request.
    """
    if not validate_input(query):
        return {"error": "Your request violates safety policies."}

    session_id = get_or_create_session(session_id)
    config = _make_config(session_id)

    with anyio.fail_after(30):
        inputs: Any = {"messages": [HumanMessage(content=query)]}
        result = graph.invoke(inputs, config=config)  # type: ignore[arg-type]

    response = result["messages"][-1].content
    if not validate_output(response):
        response = "Response blocked due to safety policy."

    return {"response": response, "session_id": session_id}
