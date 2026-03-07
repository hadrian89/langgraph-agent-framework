import importlib
import pkgutil
import app.tools


def load_tools():

    for module in pkgutil.iter_modules(app.tools.__path__):
        importlib.import_module(f"app.tools.{module.name}")