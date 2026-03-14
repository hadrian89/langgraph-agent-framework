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

        self.state = secrets.token_urlsafe(16)

        # PKCE verifier
        raw = os.urandom(32)
        self.code_verifier = base64.urlsafe_b64encode(raw).decode().rstrip("=")

        sha256 = hashlib.sha256(self.code_verifier.encode()).digest()

        self.code_challenge = base64.urlsafe_b64encode(sha256).decode().rstrip("=")

    def get_login_url(self):

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "activity heartrate location nutrition profile settings sleep social weight",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "state": self.state,
        }

        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str):

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
            "code_verifier": self.code_verifier,
        }

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)

        return response.json()
