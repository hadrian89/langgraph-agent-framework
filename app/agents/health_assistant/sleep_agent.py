from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry

SYSTEM_PROMPT = """
You are a sleep health assistant.

User query:
{query}

Sleep data:
{sleep_data}

Give helpful sleep advice.
"""


class SleepAgent:

    def __init__(self):

        self.llm = LLMGateway.get_model()
        self.tools = ToolRegistry.get_tools()

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def get_sleep_data(self):

        # Placeholder for Fitbit sleep integration
        return {"sleep_hours": 5.5, "quality": "poor"}

    def run(self, state: dict):
        """
        LangGraph node receives state
        """

        query = state.get("query", "")

        sleep_data = state.get("sleep_data") or self.get_sleep_data()

        chain = self.prompt | self.llm_with_tools

        response = chain.invoke({"query": query, "sleep_data": sleep_data})

        return {"messages": [AIMessage(content=response.content)]}

    # Make agent callable for LangGraph
    def __call__(self, state: dict):
        return self.run(state)


AgentRegistry.register(
    "health_assistant.sleep",
    SleepAgent(),
    "Handles sleep analysis, sleep advice, insomnia, fatigue",
)
