from langchain_community.tools import DuckDuckGoSearchRun
from app.core.tools_registry import ToolRegistry

search_tool = DuckDuckGoSearchRun()

ToolRegistry.register("search", search_tool)