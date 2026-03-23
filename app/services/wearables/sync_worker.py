"""
app/services/wearables/sync_worker.py

APScheduler-based Fitbit sync worker — sync implementation.
Matches your existing SessionLocal/get_db pattern from app/db.py.

Wire into main.py:
    from app.services.wearables.sync_worker import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()   # on startup
    scheduler.shutdown() # on shutdown
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.repositories.health_repository import HealthRepository
from app.repositories.token_repository import TokenRepository
from app.services.wearables.normaliser import (
    normalise_activity,
    normalise_heart_rate,
    normalise_sleep,
)
from app.tools.health_assistant.fitbit_tool import (
    FitbitClient,
    FitbitRateLimitError,
    FitbitTokenExpiredError,
)

logger = logging.getLogger(__name__)


# ── Per-user sync ────────────────────────────────────────────────────────────


def sync_user(
    user_id: str,
    db: Session,
    target_date: date | None = None,
) -> None:
    """
    Sync sleep, activity, heart_rate for one user.
    Defaults to yesterday — today's Fitbit data is often incomplete.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    token_repo = TokenRepository(db)
    token = token_repo.get_token(user_id, provider="fitbit")
    if token is None:
        logger.warning("No Fitbit token for user %s — skipping", user_id)
        return

    health_repo = HealthRepository(db)

    import httpx

    with httpx.Client(timeout=15) as http:
        client = FitbitClient(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            http=http,
        )
        try:
            _sync_sleep(client, health_repo, user_id, target_date)
            _sync_activity(client, health_repo, user_id, target_date)
            _sync_heart_rate(client, health_repo, user_id, target_date)

        except FitbitTokenExpiredError:
            logger.info("Token expired for user %s — refreshing", user_id)
            new_tokens = client.refresh_access_token()
            token_repo.update_tokens(
                user_id=user_id,
                provider="fitbit",
                access_token=new_tokens["access_token"],
                refresh_token=new_tokens["refresh_token"],
            )
            # Retry once
            _sync_sleep(client, health_repo, user_id, target_date)
            _sync_activity(client, health_repo, user_id, target_date)
            _sync_heart_rate(client, health_repo, user_id, target_date)

    db.commit()
    logger.info("Sync complete — user=%s date=%s", user_id, target_date)


# ── Per-metric helpers ───────────────────────────────────────────────────────


def _sync_sleep(client, repo, user_id, target_date):
    try:
        raw = client.get_sleep(target_date)
        normalised = normalise_sleep(raw)
        if normalised:
            repo.upsert_metric(user_id, "fitbit", "sleep", target_date, normalised)
        repo.log_sync(
            user_id, "fitbit", "sleep", "success", records_upserted=1 if normalised else 0
        )
    except FitbitRateLimitError as exc:
        repo.log_sync(user_id, "fitbit", "sleep", "rate_limited", error_message=str(exc))
        raise
    except Exception as exc:
        logger.exception("Sleep sync error user=%s", user_id)
        repo.log_sync(user_id, "fitbit", "sleep", "error", error_message=str(exc))


def _sync_activity(client, repo, user_id, target_date):
    try:
        raw = client.get_activity_summary(target_date)
        normalised = normalise_activity(raw)
        if normalised:
            repo.upsert_metric(user_id, "fitbit", "activity", target_date, normalised)
        repo.log_sync(
            user_id, "fitbit", "activity", "success", records_upserted=1 if normalised else 0
        )
    except FitbitRateLimitError as exc:
        repo.log_sync(user_id, "fitbit", "activity", "rate_limited", error_message=str(exc))
        raise
    except Exception as exc:
        logger.exception("Activity sync error user=%s", user_id)
        repo.log_sync(user_id, "fitbit", "activity", "error", error_message=str(exc))


def _sync_heart_rate(client, repo, user_id, target_date):

    try:
        raw = client.get_heart_rate(target_date)
        normalised = normalise_heart_rate(raw)
        if normalised:
            repo.upsert_metric(user_id, "fitbit", "heart_rate", target_date, normalised)
        repo.log_sync(
            user_id, "fitbit", "heart_rate", "success", records_upserted=1 if normalised else 0
        )
    except FitbitRateLimitError as exc:
        repo.log_sync(user_id, "fitbit", "heart_rate", "rate_limited", error_message=str(exc))
        raise
    except Exception as exc:
        logger.exception("Heart rate sync error user=%s", user_id)
        repo.log_sync(user_id, "fitbit", "heart_rate", "error", error_message=str(exc))


# ── Scheduled job ────────────────────────────────────────────────────────────


def run_daily_sync() -> None:
    """Nightly job — syncs all users with a stored Fitbit token."""
    from app.db.getdb import SessionLocal  # lazy import
    from app.db.models import WearableToken  # lazy import

    logger.info("Starting daily Fitbit sync")
    target_date = date.today() - timedelta(days=1)

    db = SessionLocal()
    try:
        user_ids = [
            row.user_id for row in db.query(WearableToken).filter_by(provider="fitbit").all()
        ]
    finally:
        db.close()

    logger.info("Syncing %d users for %s", len(user_ids), target_date)
    for user_id in user_ids:
        db = SessionLocal()
        try:
            sync_user(user_id, db, target_date=target_date)
        except Exception:
            logger.exception("Unhandled error syncing user %s", user_id)
            db.rollback()
        finally:
            db.close()


# ── Scheduler factory ────────────────────────────────────────────────────────


def create_scheduler() -> BackgroundScheduler:
    """
    Returns a configured APScheduler BackgroundScheduler.

    In main.py:
        scheduler = create_scheduler()
        scheduler.start()
        # on shutdown:
        scheduler.shutdown(wait=False)
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_daily_sync,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_fitbit_sync",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("APScheduler ready — daily Fitbit sync at 03:00")
    return scheduler
