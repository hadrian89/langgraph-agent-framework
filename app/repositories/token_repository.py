"""
app/repositories/token_repository.py

Sync SQLAlchemy repository for wearable_tokens.
Model matches your ACTUAL table schema:
    user_id, provider, access_token, refresh_token  (4 columns only)
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_Base = declarative_base()


class WearableToken(_Base):
    """
    Matches the actual wearable_tokens table in your DB.
    Only the 4 columns that exist — no expires_at, no updated_at.
    """

    __tablename__ = "wearable_tokens"

    user_id = Column(String(64), primary_key=True)
    provider = Column(String(32), primary_key=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)


class TokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Read ─────────────────────────────────────────────────────────────

    def get_token(
        self,
        user_id: str,
        provider: str = "fitbit",
    ) -> Optional[WearableToken]:
        """Returns token row or None if not found."""
        return self.db.query(WearableToken).filter_by(user_id=user_id, provider=provider).first()

    def get_all_for_provider(
        self,
        provider: str = "fitbit",
    ) -> list[WearableToken]:
        """All users with a token for this provider. Used by sync_worker."""
        return self.db.query(WearableToken).filter_by(provider=provider).all()

    def token_exists(self, user_id: str, provider: str = "fitbit") -> bool:
        return self.get_token(user_id, provider) is not None

    # ── Write ─────────────────────────────────────────────────────────────

    def save_token(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: str,
        commit: bool = True,
    ) -> WearableToken:
        """
        Insert or update a token row.
        Called from your Fitbit OAuth callback:

            TokenRepository(db).save_token(
                user_id, "fitbit", access_token, refresh_token
            )
            db.commit()
        """
        token = self.get_token(user_id, provider)

        if token is None:
            token = WearableToken(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
            )
            self.db.add(token)
            logger.info("Token saved — user=%s provider=%s", user_id, provider)
        else:
            token.access_token = access_token
            token.refresh_token = refresh_token
            logger.info("Token updated — user=%s provider=%s", user_id, provider)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return token

    def update_tokens(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: str,
    ) -> None:
        """
        Update tokens after a refresh flow.
        Called by sync_worker on Fitbit 401.
        Caller must db.commit() after this.
        """
        token = self.get_token(user_id, provider)
        if token is None:
            logger.error(
                "update_tokens: no token found — user=%s provider=%s",
                user_id,
                provider,
            )
            return
        token.access_token = access_token
        token.refresh_token = refresh_token
        logger.info("Tokens refreshed — user=%s provider=%s", user_id, provider)

    def delete_token(self, user_id: str, provider: str = "fitbit") -> bool:
        """Remove token — e.g. user disconnects wearable. Returns True if deleted."""
        token = self.get_token(user_id, provider)
        if token is None:
            return False
        self.db.delete(token)
        logger.info("Token deleted — user=%s provider=%s", user_id, provider)
        return True
