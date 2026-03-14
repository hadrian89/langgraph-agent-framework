import requests
from sqlalchemy.orm import Session

from app.models.health_metrics import HealthMetric


class FitbitService:

    BASE_URL = "https://api.fitbit.com/1/user/-"

    def __init__(self, access_token):
        self.access_token = access_token

    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_user_profile(self):

        url = f"{self.BASE_URL}/profile.json"

        response = requests.get(url, headers=self.headers())

        return response.json()

    def get_steps(self):

        url = f"{self.BASE_URL}/activities/steps/date/today/1d.json"

        r = requests.get(url, headers=self.headers())

        return int(r.json()["activities-steps"][0]["value"])

    def get_sleep(self):

        url = f"{self.BASE_URL}/sleep/date/today.json"

        r = requests.get(url, headers=self.headers())

        return r.json()

    def get_recent_health_data(self):

        # In a real implementation, this would fetch data from the database
        # For this example, we'll return dummy data

        return {
            "steps_history": [8500, 7000, 4200],
            "sleep_history": [6.2, 5.5, 5.1],
        }

    @staticmethod
    def get_recent_metrics(db: Session, user_id):

        return (
            db.query(HealthMetric)
            .filter(HealthMetric.user_id == user_id)
            .order_by(HealthMetric.date.desc())
            .limit(7)
            .all()
        )
