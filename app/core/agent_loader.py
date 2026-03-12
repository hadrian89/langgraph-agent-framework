import importlib
import pkgutil

import app.agents.health_assistant


def load_agents():

    for module in pkgutil.iter_modules(app.agents.health_assistant.__path__):
        importlib.import_module(f"app.agents.health_assistant.{module.name}")
