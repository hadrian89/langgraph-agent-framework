from typing import List, TypedDict

from langchain_core.messages import BaseMessage


class HealthState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    steps: int
    sleep_hours: float

    user_profile: dict
