"""OAuth2 helpers for Gmail API using Installed App Flow."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import SCOPES, TOKEN_PATH, CREDENTIALS_PATH


def load_credentials(token_path: Path = TOKEN_PATH) -> Optional[Credentials]:
    """Load stored user credentials if they exist."""
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        return creds
    return None


def store_credentials(creds: Credentials, token_path: Path = TOKEN_PATH) -> None:
    token_path.write_text(creds.to_json())


def run_oauth_flow(credentials_path: Path = CREDENTIALS_PATH) -> Credentials:
    """Trigger browser-based Installed App Flow to get new credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def refresh_credentials(creds: Credentials) -> Credentials:
    """Refresh access token using stored refresh token."""
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_gmail_service():
    """Return an authorized Gmail API service client."""
    creds = load_credentials()
    if not creds:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Missing credentials.json at {CREDENTIALS_PATH}. "
                "Download it from Google Cloud Console (OAuth client ID)."
            )
        creds = run_oauth_flow()
        store_credentials(creds)
    elif creds.expired and creds.refresh_token:
        creds = refresh_credentials(creds)
        store_credentials(creds)
    elif not creds.valid:
        # Covers revoked/invalid tokens
        creds = run_oauth_flow()
        store_credentials(creds)

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return service
