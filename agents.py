from langchain_openai import ChatOpenAI
from tools import tools

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

planner_llm = ChatOpenAI(model="gpt-4o-mini")

executor_llm = llm.bind_tools(tools)


def planner_agent(state):
    messages = state["messages"]

    plan = planner_llm.invoke(
        f"Create a short plan to answer: {messages[-1].content}"
    )

    return {"plan": plan.content}


def executor_agent(state):

    messages = state["messages"]

    response = executor_llm.invoke(messages)

    return {"messages": [response]}


def supervisor_agent(state):

    query = state["messages"][-1].content.lower()

    if "calculate" in query or "python" in query:
        return "executor"

    if "news" in query or "latest" in query:
        return "executor"

    return "executor"