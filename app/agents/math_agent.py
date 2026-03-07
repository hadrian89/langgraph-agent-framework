from app.core.agent_registry import AgentRegistry

def math_agent(state):
    return {"messages": ["Math answer"]}

AgentRegistry.register("math", math_agent)