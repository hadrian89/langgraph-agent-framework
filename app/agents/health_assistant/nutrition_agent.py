from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry

SYSTEM_PROMPT = """
You are a nutrition assistant.

User profile:
{profile}

User question:
{query}

Give a healthy meal recommendation.
"""


class NutritionAgent:

    def __init__(self):

        self.llm = LLMGateway.get_model()
        self.tools = ToolRegistry.get_tools()

        # enable tool calling
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def get_user_profile(self):
        return {"location": "UK", "diet": "vegetarian", "health_conditions": ["type2 diabetes"]}

    def __call__(self, state: dict):
        """
        LangGraph node entrypoint
        """

        messages = state["messages"]
        last_message = messages[-1]

        query = last_message.content

        profile = state.get("user_profile") or self.get_user_profile()

        chain = self.prompt | self.llm_with_tools

        response = chain.invoke({"query": query, "profile": profile})

        # return AIMessage so LangGraph can continue
        return {"messages": [AIMessage(content=response.content)]}


AgentRegistry.register(
    "health_assistant.nutrition_agent",
    NutritionAgent(),
    "Handles diet advice, meal suggestions, nutrition planning",
)
