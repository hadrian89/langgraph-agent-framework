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
            return "Search query blocked by guardrails."

    return query


def guarded_search(query):
    """
    Perform a web search using DuckDuckGo.
    """

    # Handle structured tool inputs
    if isinstance(query, dict) and "value" in query:
        query = query["value"]

    query = search_guard(query)

    return search_tool.run(query)


ToolRegistry.register("search", guarded_search)
