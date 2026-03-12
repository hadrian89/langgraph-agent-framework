class ToolRegistry:

    _tools = {}

    @classmethod
    def register(cls, name, tool):
        cls._tools[name] = tool

    @classmethod
    def get_tools(cls):
        return list(cls._tools.values())

    @classmethod
    def list_tools(cls):
        return list(cls._tools.keys())
