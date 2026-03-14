from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry

SYSTEM_PROMPT = """
You are an activity and fitness assistant.

User query:
{query}

Current activity data:
{activity_data}

Give helpful advice.
"""


class ActivityAgent:

    def __init__(self):

        self.llm = LLMGateway.get_model()
        self.tools = ToolRegistry.get_tools()

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def get_activity_data(self):
        return {"steps_today": 4200, "goal": 8000}

    def __call__(self, state):

        last_message = state["messages"][-1]
        query = last_message.content

        activity_data = self.get_activity_data()

        chain = self.prompt | self.llm_with_tools

        response = chain.invoke({"query": query, "activity_data": activity_data})

        return {"messages": [AIMessage(content=response.content)]}


AgentRegistry.register(
    "health_assistant.activity",
    ActivityAgent(),
    "Handles fitness advice, steps, walking, exercise recommendations",
)
