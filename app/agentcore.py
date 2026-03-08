from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain_core.messages import HumanMessage
from app.core.graph_builder import build_graph
from app.core.agent_loader import load_agents
from app.core.tool_loader import load_tools
from app.core.guardrails import validate_input, validate_output
from app.core.session import get_or_create_session


app = BedrockAgentCoreApp()

load_tools()
load_agents()


graph = build_graph("agentcore") # Memory management handled below

@app.entrypoint
async def handle_request(payload):
    # AgentCore automatically provides session context
    user_input = payload.get("prompt")
    session_id = get_or_create_session(payload.get("session_id"))
    if not validate_input(user_input):
        return {
            "response": "Your request violates safety policies."
        }
    print(f"Received request with session_id: {session_id} and user_input: {user_input}")
    # Pass session_id to LangGraph's config for state persistence
    config = {"configurable": {"thread_id": session_id,"actor_id": "react-agent-1", }}
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
    }
    # Invoke your existing agent logic
    result = await graph.ainvoke(
        initial_state, 
        config=config
    )
    print("Final response:", result)
    resp = result["messages"][-1].content
    if not validate_output(resp):
        resp = "Response blocked due to safety policy."
        
    return {"response": resp,"session_id": session_id}

if __name__ == "__main__":
    app.run() # Starts the AgentCore-compatible server