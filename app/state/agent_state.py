from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]
    active_agent: str  # set by the router node; routes tool results back to the correct agent
