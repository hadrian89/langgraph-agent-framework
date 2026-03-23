from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry

SYSTEM_PROMPT = """
You are a helpful personal health assistant.

User question:
{query}

Respond in a helpful and concise way.
"""


class ConversationAgent:

    def __init__(self):

        self.llm = LLMGateway.get_model()
        self.tools = ToolRegistry.get_tools()

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def run(self, state: dict):
        """
        LangGraph node receives state dict
        """

        query = state.get("query", "")

        chain = self.prompt | self.llm_with_tools

        response = chain.invoke({"query": query})

        return {"messages": [AIMessage(content=response.content)]}

    # Make agent callable for LangGraph
    def __call__(self, state: dict):
        return self.run(state)


AgentRegistry.register(
    "health_assistant.conversation_agent",
    ConversationAgent(),
    "General health questions and conversation",
)
