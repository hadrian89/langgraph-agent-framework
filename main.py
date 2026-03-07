from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from graph import build_graph

app = FastAPI()

graph = build_graph()


@app.post("/chat")
def chat(query: str):

    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]}
    )

    return {"response": result["messages"][-1].content}