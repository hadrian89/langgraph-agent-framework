from app.core.tools_registry import ToolRegistry


def get_daily_steps():
    """
    Gets the daily step count for a user from Fitbit API. This is a mock implementation.
    In a real implementation, you would make an API call to Fitbit's endpoint with the user's
    access token and return the actual step count.
    """
    return {"steps": 4200, "goal": 8000}


ToolRegistry.register("fitbit_steps", get_daily_steps)
