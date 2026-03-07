from langchain_community.tools import DuckDuckGoSearchRun
from app.core.tools_registry import ToolRegistry

search_tool = DuckDuckGoSearchRun()


BLOCKED_SEARCH_PATTERNS = [
    "system prompt",
    "internal prompt",
    "ignore previous instructions",
    "reveal system prompt",
    "bypass guardrails",
]


MAX_QUERY_LENGTH = 200


def search_guard(query: str):

    q = query.lower().strip()

    if len(q) > MAX_QUERY_LENGTH:
        raise ValueError("Search query too long")

    for pattern in BLOCKED_SEARCH_PATTERNS:
        if pattern in q:
            raise ValueError("Search query blocked by guardrails")

    return query


def guarded_search(query: str):
    """
    Perform a web search using DuckDuckGo.
    Use this tool for retrieving factual information,
    news, or general knowledge from the internet.
    """

    query = search_guard(query)

    return search_tool.run(query)


ToolRegistry.register("search", guarded_search)