from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway


llm = LLMGateway.get_model()

SYSTEM_PROMPT = """
You are a programming assistant.

Rules:
- Always return code inside markdown code blocks.
- Use proper language tags like ```python
- If explaining code, explain AFTER the code block.
"""

def format_code(text):

    if "def " in text or "import " in text:

        return f"```python\n{text}\n```"

    return text


def coding_agent(state):

    response = llm.invoke(state["messages"])

    return {"messages": [response]}


AgentRegistry.register("coding", coding_agent,"Handles programming, algorithms, debugging, and code generation")