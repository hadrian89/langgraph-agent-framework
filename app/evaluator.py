def evaluate_response(state):

    result = state["messages"][-1].content

    if not result or len(result) < 10:
        return {"result": "Response too short"}

    return {"result": result}