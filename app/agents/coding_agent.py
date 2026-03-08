from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway

SYSTEM_PROMPT = """
You are a programming assistant.

Rules:
- Always return code inside markdown code blocks.
- Use proper language tags like ```python
- If explaining code, explain AFTER the code block.
"""


def coding_agent(state):
    llm = LLMGateway.get_model()

    response = llm.invoke(state["messages"])

    return {"messages": [response]}


AgentRegistry.register("coding", coding_agent, SYSTEM_PROMPT)
