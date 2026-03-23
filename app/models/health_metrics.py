from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(String(64), nullable=False)
    provider = Column(String(32), nullable=False, default="fitbit")

    metric_type = Column(String(32), nullable=False)  # sleep, activity, heart_rate
    recorded_date = Column(Date, nullable=False)

    data = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            "metric_type",
            "recorded_date",
            name="uq_health_metrics_user_provider_type_date",
        ),
        Index("ix_health_metrics_user_type", "user_id", "metric_type"),
        Index("ix_health_metrics_user_date", "user_id", "recorded_date"),
    )


class WearableSyncLog(Base):
    __tablename__ = "wearable_sync_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(String(64), nullable=False, index=True)
    provider = Column(String(32), nullable=False)

    sync_type = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False)

    records_upserted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    synced_at = Column(DateTime(timezone=True), server_default=func.now())
