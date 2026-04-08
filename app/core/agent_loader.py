import importlib
import pkgutil

import app.agents


def load_agents():
    """
    Auto-discover and import every module directly inside app/agents/.

    Importing each module triggers its AgentRegistry.register() call at
    module level — no manual wiring needed.
    """
    for module_info in pkgutil.iter_modules(app.agents.__path__):
        importlib.import_module(f"app.agents.{module_info.name}")
