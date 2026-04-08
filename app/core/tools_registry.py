from typing import Callable, List


class ToolRegistry:
    """
    Central registry for all tools.

    Tools are plain Python callables with a docstring — LangChain converts them
    to StructuredTool automatically when passed to llm.bind_tools().

    Example
    -------
    ToolRegistry.register("search", guarded_search)
    """

    _tools: dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str, tool: Callable) -> None:
        cls._tools[name] = tool

    @classmethod
    def get_tool(cls, name: str) -> Callable:
        """Return a single tool by name. Raises KeyError if not registered."""
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return cls._tools[name]

    @classmethod
    def get_tools(cls) -> List[Callable]:
        """Return all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_tools_by_names(cls, names: List[str]) -> List[Callable]:
        """Return only the tools whose names are in the provided list."""
        missing = [n for n in names if n not in cls._tools]
        if missing:
            raise KeyError(f"Tools not registered: {missing}")
        return [cls._tools[n] for n in names]

    @classmethod
    def list_tools(cls) -> List[str]:
        return list(cls._tools.keys())
