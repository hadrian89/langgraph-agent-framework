class AgentRegistry:

    _agents = {}
    _metadata = {}

    @classmethod
    def register(cls, name, agent_fn, description=""):
        cls._agents[name] = agent_fn
        cls._metadata[name] = description

    @classmethod
    def get_agent(cls, name):
        return cls._agents[name]

    @classmethod
    def list_agents(cls):
        return list(cls._agents.keys())

    @classmethod
    def all_agents(cls):
        return cls._agents

    @classmethod
    def get_metadata(cls):
        return cls._metadata