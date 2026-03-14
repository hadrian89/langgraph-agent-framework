from app.core.tools_registry import ToolRegistry
from app.services.wearables.fitbit_service import FitbitService


def get_health_summary():
    """
    Return recent wearable health metrics including steps and sleep history.
    """
    service = FitbitService("USER_ACCESS_TOKEN")
    return service.get_recent_health_data()


def get_daily_steps():
    """
    Return the user's total steps for the current day from wearable device.
    """

    return {"steps_today": "4200", "goal": "8000"}


def get_sleep_data():
    """
    Return sleep metrics including hours slept and sleep quality from wearable device.
    """
    service = FitbitService("USER_ACCESS_TOKEN")

    return service.get_sleep()


ToolRegistry.register("get_daily_steps", get_daily_steps)
ToolRegistry.register("get_sleep_data", get_sleep_data)
