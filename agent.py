from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graph import build_graph

graph = build_graph()

print("\nLangGraph Agent Ready (type 'exit' to quit)\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    result = graph.invoke(
        {"messages": [HumanMessage(content=user_input)]}
    )

    print("Agent:", result["messages"][-1].content)