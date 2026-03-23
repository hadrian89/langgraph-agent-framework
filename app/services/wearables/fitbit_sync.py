"""
app/services/wearables/fitbit_sync.py

Initial Fitbit data sync — called once after OAuth callback.
Uses FitbitService.get_steps() and get_sleep() which already exist.
"""

from datetime import date

from app.db.getdb import SessionLocal
from app.repositories.health_repository import HealthRepository
from app.services.wearables.fitbit_service import FitbitService
from app.services.wearables.normaliser import normalise_sleep


def sync_fitbit_data(user_id: str, access_token: str) -> None:
    """
    Fetches today's sleep + activity from Fitbit and upserts
    into health_metrics as two separate JSONB rows.
    Called from /redirect callback immediately after OAuth.
    """
    service = FitbitService(access_token)
    today = date.today()
    db = SessionLocal()

    try:
        repo = HealthRepository(db)

        # ── Sleep ─────────────────────────────────────────────────────────
        try:
            raw_sleep = service.get_sleep()  # returns full Fitbit JSON
            normalised_sleep = normalise_sleep(raw_sleep)
            if normalised_sleep:
                repo.upsert_metric(user_id, "fitbit", "sleep", today, normalised_sleep)
                repo.log_sync(user_id, "fitbit", "sleep", "success", records_upserted=1)
                print(f"Sleep synced — user={user_id} minutes={normalised_sleep['minutes_asleep']}")
            else:
                print(f"No sleep data for {today}")
                repo.log_sync(user_id, "fitbit", "sleep", "success", records_upserted=0)
        except Exception as exc:
            print(f"Sleep sync failed: {exc}")
            repo.log_sync(user_id, "fitbit", "sleep", "error", error_message=str(exc))

        # ── Activity (steps) ──────────────────────────────────────────────
        try:
            steps = service.get_steps()  # returns int directly
            activity_data = {
                "steps": steps,
                "calories_out": 0,  # not available from this endpoint
                "sedentary_minutes": 0,
                "lightly_active_minutes": 0,
                "fairly_active_minutes": 0,
                "very_active_minutes": 0,
                "total_active_minutes": 0,
                "distance_km": 0.0,
                "floors": 0,
            }
            repo.upsert_metric(user_id, "fitbit", "activity", today, activity_data)
            repo.log_sync(user_id, "fitbit", "activity", "success", records_upserted=1)
            print(f"Activity synced — user={user_id} steps={steps}")
        except Exception as exc:
            print(f"Activity sync failed: {exc}")
            repo.log_sync(user_id, "fitbit", "activity", "error", error_message=str(exc))

        db.commit()
        print(f"Fitbit sync completed — user={user_id}")

    except Exception as exc:
        db.rollback()
        print(f"Fitbit sync rolled back: {exc}")
        raise
    finally:
        db.close()
