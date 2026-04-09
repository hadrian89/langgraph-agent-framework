import importlib
import pkgutil

import app.tools


def load_tools():
    """
    Auto-discover and import every module directly inside app/tools/.

    Importing each module triggers its ToolRegistry.register() call at
    module level — no manual wiring needed.
    """
    for module_info in pkgutil.iter_modules(app.tools.__path__):
        importlib.import_module(f"app.tools.{module_info.name}")
