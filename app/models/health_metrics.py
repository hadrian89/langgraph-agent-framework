from sqlalchemy import TIMESTAMP, Column, Date, Float, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class HealthMetric(Base):

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String)

    date = Column(Date)

    steps = Column(Integer)

    sleep_hours = Column(Float)

    sleep_score = Column(Integer)

    resting_heart_rate = Column(Integer)

    calories_burned = Column(Integer)

    created_at = Column(TIMESTAMP, server_default=func.now())
