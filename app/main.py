import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router
from app.repositories.token_repository import save_fitbit_tokens
from app.services.wearables.fitbit_oauth import FitbitOAuth
from app.services.wearables.fitbit_service import FitbitService
from app.services.wearables.fitbit_sync import sync_fitbit_data

load_dotenv()

app = FastAPI(title="Agent Framework Platform", version="1.0.0")

app.include_router(router)


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


@app.get("/fitbit/login")
def fitbit_login():
    login_url = fitbit.get_login_url()

    return {"login_url": login_url}


@app.get("/redirect")
def fitbit_callback(code: str):

    token_response = fitbit.exchange_code(code)

    access_token = token_response["access_token"]

    refresh_token = token_response["refresh_token"]

    service = FitbitService(access_token)

    profile = service.get_user_profile()

    user_id = profile["user"]["encodedId"]

    print("Fitbit User:", user_id)

    save_fitbit_tokens(
        user_id,
        access_token,
        refresh_token,
    )

    # auto trigger sync
    sync_fitbit_data(user_id, access_token)

    return {
        "status": "Fitbit connected",
        "user_id": user_id,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
