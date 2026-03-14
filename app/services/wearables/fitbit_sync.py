from datetime import date

from sqlalchemy import text

from app.db import SessionLocal
from app.services.wearables.fitbit_service import FitbitService


def sync_fitbit_data(user_id, access_token):

    service = FitbitService(access_token)

    steps = service.get_steps()

    sleep = service.get_sleep()

    sleep_hours = sleep["summary"]["totalMinutesAsleep"] / 60

    db = SessionLocal()

    db.execute(
        text(
            """
        INSERT INTO health_metrics
        (user_id, date, steps, sleep_hours)
        VALUES (:user_id,:date,:steps,:sleep)
        """
        ),
        {
            "user_id": user_id,
            "date": date.today(),
            "steps": steps,
            "sleep": sleep_hours,
        },
    )

    db.commit()

    db.close()

    print("Fitbit sync completed")
