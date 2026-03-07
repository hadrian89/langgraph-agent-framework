from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from app.graph import build_graph

from dotenv import load_dotenv
load_dotenv()

from app.core.telemetry import tracer

from app.core.agent_loader import load_agents
from app.core.tool_loader import load_tools

load_tools()
load_agents()

app = FastAPI()

graph = build_graph()


@app.post("/chat")
def chat(query: str):
    with tracer.start_as_current_span("agent_request"):

        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]}
        )

        return {"response": result["messages"][-1].content}