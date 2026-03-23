"""
app/tools/health_assistant/fitbit_tool.py

Fitbit API client (sync, using httpx.Client) + LangChain StructuredTools.
Sits alongside your existing wearable_tools.py, nutrition_tool.py etc.
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any, Optional

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

FITBIT_API_BASE = "https://api.fitbit.com"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_CLIENT_ID = os.environ.get("FITBIT_CLIENT_ID", "")
FITBIT_CLIENT_SECRET = os.environ.get("FITBIT_CLIENT_SECRET", "")


class FitbitTokenExpiredError(Exception):
    pass


class FitbitRateLimitError(Exception):
    pass


class FitbitClient:
    """
    Sync Fitbit HTTP client.

    Can be used standalone (pass http=httpx.Client()) or via the
    sync_worker which manages the httpx.Client lifecycle.
    """

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        http: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._http = http or httpx.Client(timeout=15)
        self._owns_http = http is None

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "FitbitClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, url: str) -> dict[str, Any]:
        resp = self._http.get(url, headers=self._headers())
        if resp.status_code == 401:
            raise FitbitTokenExpiredError("Access token expired")
        if resp.status_code == 429:
            raise FitbitRateLimitError("Fitbit rate limit exceeded")
        resp.raise_for_status()
        return resp.json()

    def refresh_access_token(self) -> dict[str, str]:
        resp = self._http.post(
            FITBIT_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": FITBIT_CLIENT_ID,
            },
            auth=(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        tokens = resp.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        logger.info("Fitbit tokens refreshed")
        return tokens

    def get_user_profile(self) -> dict[str, Any]:
        return self._get(f"{FITBIT_API_BASE}/1/user/-/profile.json")

    def get_sleep(self, target_date: date) -> dict[str, Any]:
        return self._get(f"{FITBIT_API_BASE}/1.2/user/-/sleep/date/{target_date:%Y-%m-%d}.json")

    def get_activity_summary(self, target_date: date) -> dict[str, Any]:
        return self._get(f"{FITBIT_API_BASE}/1/user/-/activities/date/{target_date:%Y-%m-%d}.json")

    def get_heart_rate(self, target_date: date) -> dict[str, Any]:
        return self._get(
            f"{FITBIT_API_BASE}/1/user/-/activities/heart/date/{target_date:%Y-%m-%d}/1d.json"
        )


# ── LangChain tool schemas ───────────────────────────────────────────────────


class DateInput(BaseModel):
    user_id: str = Field(description="Fitbit encodedId of the user e.g. BXZPNX")
    date_str: Optional[str] = Field(
        default=None,
        description="Date YYYY-MM-DD. Defaults to yesterday if omitted.",
    )


def _resolve_date(date_str: str | None) -> date:
    return date.fromisoformat(date_str) if date_str else date.today() - timedelta(days=1)


def _get_sleep(user_id: str, date_str: str | None = None) -> str:
    from app.db import SessionLocal
    from app.repositories.token_repository import TokenRepository
    from app.services.wearables.normaliser import normalise_sleep

    db = SessionLocal()
    try:
        token = TokenRepository(db).get_token(user_id, "fitbit")
        if not token:
            return f"No Fitbit token for user {user_id}"
    finally:
        db.close()

    with FitbitClient(token.access_token, token.refresh_token) as client:
        raw = client.get_sleep(_resolve_date(date_str))
    result = normalise_sleep(raw)
    return str(result) if result else "No sleep data found"


def _get_activity(user_id: str, date_str: str | None = None) -> str:
    from app.db.getdb import SessionLocal
    from app.repositories.token_repository import TokenRepository
    from app.services.wearables.normaliser import normalise_activity

    db = SessionLocal()
    try:
        token = TokenRepository(db).get_token(user_id, "fitbit")
        if not token:
            return f"No Fitbit token for user {user_id}"
    finally:
        db.close()

    with FitbitClient(token.access_token, token.refresh_token) as client:
        raw = client.get_activity_summary(_resolve_date(date_str))
    result = normalise_activity(raw)
    return str(result) if result else "No activity data found"


def _get_heart_rate(user_id: str, date_str: str | None = None) -> str:
    from app.db import SessionLocal
    from app.repositories.token_repository import TokenRepository
    from app.services.wearables.normaliser import normalise_heart_rate

    db = SessionLocal()
    try:
        token = TokenRepository(db).get_token(user_id, "fitbit")
        if not token:
            return f"No Fitbit token for user {user_id}"
    finally:
        db.close()

    with FitbitClient(token.access_token, token.refresh_token) as client:
        raw = client.get_heart_rate(_resolve_date(date_str))
    result = normalise_heart_rate(raw)
    return str(result) if result else "No heart rate data found"


# ── Exported StructuredTools ─────────────────────────────────────────────────

fitbit_get_sleep = StructuredTool.from_function(
    func=_get_sleep,
    name="fitbit_get_sleep",
    description=(
        "Fetch sleep data for a user from Fitbit. "
        "Returns minutes asleep, efficiency, sleep stages (deep/light/REM/wake)."
    ),
    args_schema=DateInput,
)

fitbit_get_activity = StructuredTool.from_function(
    func=_get_activity,
    name="fitbit_get_activity",
    description=(
        "Fetch daily activity summary from Fitbit. "
        "Returns steps, calories, active minutes, distance."
    ),
    args_schema=DateInput,
)

fitbit_get_heart_rate = StructuredTool.from_function(
    func=_get_heart_rate,
    name="fitbit_get_heart_rate",
    description=(
        "Fetch heart rate data from Fitbit. "
        "Returns resting heart rate and heart rate zone minutes."
    ),
    args_schema=DateInput,
)
