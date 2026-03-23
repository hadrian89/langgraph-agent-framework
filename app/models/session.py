from sqlalchemy import Column, DateTime, Index, String, func

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(128), primary_key=True)
    user_id = Column(String(64), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)
