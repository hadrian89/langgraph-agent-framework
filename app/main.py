"""
app/main.py
"""

import os

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router
from app.core.auth import SessionRepository
from app.db.getdb import SessionLocal
from app.repositories.token_repository import TokenRepository
from app.services.wearables.fitbit_oauth import FitbitOAuth
from app.services.wearables.fitbit_service import FitbitService
from app.services.wearables.fitbit_sync import sync_fitbit_data
from app.services.wearables.sync_worker import create_scheduler

load_dotenv()

app = FastAPI(title="Agent Framework Platform", version="1.0.0")
app.include_router(router)

db = SessionLocal()

client_id = os.getenv("FITBIT_CLIENT_ID")
if not client_id:
    raise ValueError("FITBIT_CLIENT_ID environment variable is not set")

client_secret = os.getenv("FITBIT_CLIENT_SECRET")
if not client_secret:
    raise ValueError("FITBIT_CLIENT_SECRET environment variable is not set")

redirect_uri = os.getenv("FITBIT_REDIRECT_URI")
if not redirect_uri:
    raise ValueError("FITBIT_REDIRECT_URI environment variable is not set")

fitbit = FitbitOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
)

scheduler: BackgroundScheduler | None = None


@app.on_event("startup")
def startup():
    global scheduler
    scheduler = create_scheduler()
    scheduler.start()


@app.on_event("shutdown")
def shutdown():
    if scheduler:
        scheduler.shutdown(wait=False)


@app.get("/fitbit/login")
def fitbit_login():
    return {"login_url": fitbit.get_login_url()}


@app.get("/redirect")
def fitbit_callback(code: str):
    # 1. Exchange code for tokens
    token_response = fitbit.exchange_code(code)
    print("Token response:", token_response)  # ← add this
    access_token = token_response["access_token"]
    refresh_token = token_response["refresh_token"]

    # 2. Get Fitbit user identity
    service = FitbitService(access_token)
    profile = service.get_user_profile()
    user_id = profile["user"]["encodedId"]
    print("Fitbit User:", user_id)

    # 3. Persist tokens
    TokenRepository(db).save_token(user_id, "fitbit", access_token, refresh_token, commit=True)

    # 4. Create a session for this user  ← NEW
    session_id = SessionRepository(db).create_session(user_id)

    db.commit()

    # 5. Trigger initial data sync
    sync_fitbit_data(user_id, access_token)

    # 6. Return session_id to the client — store this and send with /chat requests
    return {
        "status": "Fitbit connected",
        "user_id": user_id,
        "session_id": session_id,  # ← client stores this
    }


@app.get("/health")
def health():
    return {"status": "ok"}
