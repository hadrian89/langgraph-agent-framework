"""
app/services/wearables/fitbit_oauth.py

PKCE values (code_verifier, code_challenge, state) are regenerated
on every get_login_url() call — not at __init__ time.
This fixes the re-authentication bug where the verifier becomes
stale after the first login.
"""

import base64
import hashlib
import os
import secrets
import urllib.parse

import requests


class FitbitOAuth:

    AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
    TOKEN_URL = "https://api.fitbit.com/oauth2/token"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # These are set fresh on every get_login_url() call
        self._state: str | None = None
        self._code_verifier: str | None = None

    def _generate_pkce(self) -> str:
        """Generate fresh PKCE verifier + challenge. Returns challenge."""
        self._state = secrets.token_urlsafe(16)

        raw = os.urandom(32)
        self._code_verifier = base64.urlsafe_b64encode(raw).decode().rstrip("=")

        sha256 = hashlib.sha256(self._code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(sha256).decode().rstrip("=")

    def get_login_url(self) -> str:
        """
        Generates a fresh login URL with new PKCE values every time.
        Must be called before exchange_code() to ensure verifier matches.
        """
        code_challenge = self._generate_pkce()

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "activity heartrate location nutrition profile settings sleep social weight",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": self._state,
        }

        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        """
        Exchange the authorization code for tokens.
        Uses the code_verifier from the most recent get_login_url() call.
        """
        if not self._code_verifier:
            raise ValueError("No code_verifier found. Call get_login_url() before exchange_code().")

        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
            "code_verifier": self._code_verifier,
        }

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        result = response.json()

        # Surface Fitbit errors clearly instead of KeyError later
        if "access_token" not in result:
            error = result.get("errors", result.get("error", "unknown error"))
            raise ValueError(f"Fitbit token exchange failed: {error}")

        # Clear verifier after use — prevents reuse of same code
        self._code_verifier = None

        return result
