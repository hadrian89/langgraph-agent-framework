from collections import defaultdict


class HealthMemory:

    def __init__(self):

        self.memory = defaultdict(list)

    def add_message(self, session_id, role, message):

        self.memory[session_id].append({"role": role, "message": message})

    def get_history(self, session_id):

        return self.memory.get(session_id, [])
