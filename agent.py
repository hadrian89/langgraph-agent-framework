from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graph import build_graph

graph = build_graph()

print("\nMulti-Agent System Ready\n")

while True:

    query = input("You: ")

    if query == "exit":
        break

    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]}
    )
    print(result)

    print("\nAgent:", result["messages"][-1].content or "[tool executed]")