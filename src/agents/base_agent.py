
class BaseAgent:
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.enabled = True
        self.last_result = None  # always a dict

    def run(self, **kwargs):
        raise NotImplementedError

    def to_dict(self):
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "last_result": self.last_result,
        }
