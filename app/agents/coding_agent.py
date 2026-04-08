from langchain_core.messages import SystemMessage

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.logging import logger
from app.core.tracing import trace_node

_SYSTEM_PROMPT = """You are an expert programming assistant.

Rules:
- Always wrap code in markdown code blocks with the correct language tag (e.g. ```python).
- Provide a brief explanation AFTER the code block, never before.
- If the request is ambiguous, write the simplest correct solution and note any assumptions.
"""


@trace_node("coding_agent")
def coding_agent(state: dict) -> dict:
    llm = LLMGateway.get_model()

    messages = [SystemMessage(content=_SYSTEM_PROMPT)] + list(state["messages"])
    logger.info("coding_agent invoked")
    response = llm.invoke(messages)
    return {"messages": [response]}


AgentRegistry.register(
    name="coding",
    agent_fn=coding_agent,
    description="Writes, explains, debugs, and reviews code in any programming language",
    tools=[],  # coding agent works purely from LLM knowledge — no external tools needed
)
