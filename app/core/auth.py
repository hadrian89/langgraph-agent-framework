"""
app/core/auth.py

Session-based auth for the agent API.

Flow:
    1. User hits /fitbit/login → OAuth → /redirect callback
    2. Callback creates a session row, returns session_id to client
    3. Client sends session_id on every subsequent request:
           Authorization: Bearer <session_id>
        or X-Session-ID: <session_id>
    4. get_current_user() dependency resolves session_id → user_id
    5. user_id flows into LangGraph state → agents query only that user's data
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from app.db.getdb import get_db

logger = logging.getLogger(__name__)

_Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM model — matches your sessions table
#   session_id | user_id | created_at
# ---------------------------------------------------------------------------


class UserSession(_Base):
    __tablename__ = "sessions"

    session_id = Column(String(128), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# SessionRepository
# ---------------------------------------------------------------------------


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, user_id: str) -> str:
        """
        Create a new session row and return the session_id.

        Call this at the END of your /redirect callback:

            session_id = SessionRepository(db).create_session(user_id)
            db.commit()
            return {"status": "connected", "session_id": session_id}

        The client stores session_id and sends it with every /chat request.
        """
        session_id = str(uuid.uuid4())
        self.db.add(UserSession(session_id=session_id, user_id=user_id))
        logger.info("Session created — user=%s session=%s", user_id, session_id)
        return session_id

    def get_user_id(self, session_id: str) -> Optional[str]:
        """Resolve session_id → user_id. Returns None if not found."""
        row = self.db.query(UserSession).filter_by(session_id=session_id).first()
        return row.user_id if row else None

    def delete_session(self, session_id: str) -> None:
        """Logout — remove the session."""
        self.db.query(UserSession).filter_by(session_id=session_id).delete()
        self.db.commit()
        logger.info("Session deleted — session=%s", session_id)


# ---------------------------------------------------------------------------
# FastAPI dependency — use this in any protected route
# ---------------------------------------------------------------------------


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_session_id: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """
    Resolves the current user_id from the session.

    Clients send the session_id received from /redirect in one of:
        Authorization: Bearer <session_id>
        X-Session-ID: <session_id>

    Usage in any protected route:
        @router.post("/chat")
        def chat(
            request: ChatRequest,
            user_id: str = Depends(get_current_user),
            db: Session = Depends(get_db),
        ):
            result = graph.invoke(
                {"messages": [...], "user_id": user_id},
                config={"configurable": {"thread_id": user_id}},
            )
    """
    session_id = _extract_session_id(authorization, x_session_id)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session ID provided. Connect via /fitbit/login first.",
        )

    user_id = SessionRepository(db).get_user_id(session_id)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired. Reconnect via /fitbit/login.",
        )

    logger.debug("Authenticated — user=%s session=%s", user_id, session_id)
    return user_id


def _extract_session_id(
    authorization: Optional[str],
    x_session_id: Optional[str],
) -> Optional[str]:
    if x_session_id:
        return x_session_id.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None
