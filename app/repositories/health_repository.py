"""
app/repositories/health_repository.py

Sync SQLAlchemy repository for health_metrics and wearable_sync_log.
Matches your existing db.py pattern (SessionLocal, sync sessionmaker).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.health_metrics import HealthMetric, WearableSyncLog

logger = logging.getLogger(__name__)


class HealthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Write ───────────────────────────────────────────────────────────────

    def upsert_metric(
        self,
        user_id: str,
        provider: str,
        metric_type: str,
        recorded_date: date,
        data: dict[str, Any],
    ) -> None:
        """Idempotent — re-syncing the same date never creates duplicates."""
        stmt = (
            pg_insert(HealthMetric)
            .values(
                user_id=user_id,
                provider=provider,
                metric_type=metric_type,
                recorded_date=recorded_date,
                data=data,
            )
            .on_conflict_do_update(
                constraint="uq_health_metrics_user_provider_type_date",
                set_={"data": data, "updated_at": datetime.utcnow()},
            )
        )
        self.db.execute(stmt)

    def log_sync(
        self,
        user_id: str,
        provider: str,
        sync_type: str,
        status: str,
        records_upserted: int = 0,
        error_message: str | None = None,
    ) -> None:
        self.db.add(
            WearableSyncLog(
                user_id=user_id,
                provider=provider,
                sync_type=sync_type,
                status=status,
                records_upserted=records_upserted,
                error_message=error_message,
            )
        )

    # ── Read ────────────────────────────────────────────────────────────────

    def get_metrics(
        self,
        user_id: str,
        metric_type: str,
        days: int = 7,
    ) -> list[HealthMetric]:
        """Last `days` days of a metric, ordered oldest → newest."""
        since = date.today() - timedelta(days=days)
        return (
            self.db.query(HealthMetric)
            .filter(
                HealthMetric.user_id == user_id,
                HealthMetric.metric_type == metric_type,
                HealthMetric.recorded_date >= since,
            )
            .order_by(HealthMetric.recorded_date.asc())
            .all()
        )

    def get_latest_metric(
        self,
        user_id: str,
        metric_type: str,
    ) -> HealthMetric | None:
        return (
            self.db.query(HealthMetric)
            .filter(
                HealthMetric.user_id == user_id,
                HealthMetric.metric_type == metric_type,
            )
            .order_by(HealthMetric.recorded_date.desc())
            .first()
        )
