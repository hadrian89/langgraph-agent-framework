import uuid

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class WearableToken(Base):
    __tablename__ = "wearable_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, nullable=False)
    provider = Column(String(50), nullable=False)

    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)

    expires_at = Column(DateTime)
    scope = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "provider"),)
