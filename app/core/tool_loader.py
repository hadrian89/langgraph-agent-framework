import importlib
import pkgutil

import app.tools.health_assistant


def load_tools():

    for module in pkgutil.iter_modules(app.tools.health_assistant.__path__):
        importlib.import_module(f"app.tools.health_assistant.{module.name}")
