import importlib
import pkgutil

import app.agents


def load_agents():

    for module in pkgutil.iter_modules(app.agents.__path__):
        importlib.import_module(f"app.agents.{module.name}")
