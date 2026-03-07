from app.core.tracing import trace_node


@trace_node("router")
def route(state):

    query = state["messages"][-1].content.lower()

    if "code" in query or "python" in query:
        return "coding"

    return "search"