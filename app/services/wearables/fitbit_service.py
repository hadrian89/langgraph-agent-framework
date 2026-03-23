"""
app/services/wearables/fitbit_service.py

Extended FitbitService — keeps all existing methods unchanged,
adds get_activity_summary() and get_heart_rate() for the sync worker.
"""

import requests


class FitbitService:

    BASE_URL = "https://api.fitbit.com/1/user/-"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ── Existing methods — unchanged ──────────────────────────────────────

    def get_user_profile(self) -> dict:
        url = f"{self.BASE_URL}/profile.json"
        return requests.get(url, headers=self.headers()).json()

    def get_steps(self) -> int:
        url = f"{self.BASE_URL}/activities/steps/date/today/1d.json"
        r = requests.get(url, headers=self.headers())
        return int(r.json()["activities-steps"][0]["value"])

    def get_sleep(self) -> dict:
        url = f"{self.BASE_URL}/sleep/date/today.json"
        return requests.get(url, headers=self.headers()).json()

    def get_recent_health_data(self) -> dict:
        return {
            "steps_history": [8500, 7000, 4200],
            "sleep_history": [6.2, 5.5, 5.1],
        }

    # ── New methods — used by sync_worker and fitbit_tool ─────────────────

    def get_activity_summary(self, date_str: str = "today") -> dict:
        """
        Full activity summary for a given date.
        Returns Fitbit /activities/date/{date}.json response.
        normalise_activity() consumes this.
        """
        url = f"{self.BASE_URL}/activities/date/{date_str}.json"
        return requests.get(url, headers=self.headers()).json()

    def get_heart_rate(self, date_str: str = "today") -> dict:
        """
        Heart rate summary for a given date.
        Returns Fitbit /activities/heart/date/{date}/1d.json response.
        normalise_heart_rate() consumes this.
        """
        url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{date_str}/1d.json"
        return requests.get(url, headers=self.headers()).json()

    def get_sleep_by_date(self, date_str: str) -> dict:
        """
        Sleep for a specific date (YYYY-MM-DD).
        get_sleep() always fetches today — use this for historical sync.
        """
        url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{date_str}.json"
        return requests.get(url, headers=self.headers()).json()
