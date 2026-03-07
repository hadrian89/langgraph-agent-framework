from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway


llm = LLMGateway.get_model()


def coding_agent(state):

    response = llm.invoke(state["messages"])

    return {"messages": [response]}


AgentRegistry.register("coding", coding_agent,"Handles programming, algorithms, debugging, and code generation")