class AgentRegistry:

    _agents = {}

    @classmethod
    def register(cls, name, agent_fn):
        cls._agents[name] = agent_fn

    @classmethod
    def get_agent(cls, name):
        return cls._agents[name]

    @classmethod
    def list_agents(cls):
        return list(cls._agents.keys())

    @classmethod
    def all_agents(cls):
        return cls._agents