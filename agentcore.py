from typing import Any, cast

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain_core.messages import HumanMessage

from app.core.agent_loader import load_agents
from app.core.graph_builder import build_graph
from app.core.guardrails import validate_input, validate_output
from app.core.session import get_or_create_session
from app.core.tool_loader import load_tools

app = BedrockAgentCoreApp()

load_tools()
load_agents()


graph = build_graph("agentcore")  # Memory management handled below


@app.entrypoint
async def handle_request(payload, context):
    # AgentCore automatically provides session context
    user_input = payload.get("prompt")
    session_id = payload.get("session_id") or context.session_id
    session_id = get_or_create_session(session_id)
    print(f"Received request: {user_input} with session_id: {session_id}")
    if not validate_input(user_input):
        return {"response": "Your request violates safety policies."}

    # Pass session_id to LangGraph's config for state persistence
    config = {
        "configurable": {
            "thread_id": session_id,
            "actor_id": "react-agent-1",
        }
    }
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
    }
    # Invoke your existing agent logic
    result = await graph.ainvoke(cast(Any, initial_state), config=cast(Any, config))
    print("Final response:", result)
    resp = result["messages"][-1].content
    if not validate_output(resp):
        resp = "Response blocked due to safety policy."

    return {"response": resp, "session_id": session_id}


if __name__ == "__main__":
    app.run()  # Starts the AgentCore-compatible server
