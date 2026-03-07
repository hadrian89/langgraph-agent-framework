from langchain_openai import ChatOpenAI
from tools import tools

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

search_agent = llm.bind_tools(tools)

finance_agent = ChatOpenAI(model="gpt-4o-mini")

coding_agent = ChatOpenAI(model="gpt-4o-mini")


def search_node(state):
    response = search_agent.invoke(state["messages"])
    return {"messages": [response]}


def finance_node(state):
    response = finance_agent.invoke(state["messages"])
    return {"messages": [response]}


def coding_node(state):
    response = coding_agent.invoke(state["messages"])
    return {"messages": [response]}