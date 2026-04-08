import requests

from app.core.tools_registry import ToolRegistry

_WTTR_URL = "https://wttr.in/{location}?format=3"
_TIMEOUT = 8  # seconds


def get_weather(location: str) -> str:
    """
    Get the current weather for a city or location.

    Returns a one-line summary such as:
        London: ⛅️  +14°C

    Uses the free wttr.in service — no API key required.
    """
    location = location.strip()
    if not location:
        return "Please provide a location to get weather for."

    try:
        response = requests.get(_WTTR_URL.format(location=location), timeout=_TIMEOUT)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.Timeout:
        return f"Weather request timed out for '{location}'. Please try again."
    except requests.exceptions.HTTPError as exc:
        return f"Could not fetch weather for '{location}': {exc}"
    except requests.exceptions.RequestException as exc:
        return f"Network error while fetching weather: {exc}"


ToolRegistry.register("weather", get_weather)
