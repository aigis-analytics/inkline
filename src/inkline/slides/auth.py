"""Google API authentication — OAuth2 and service account support."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Scopes required for Slides + Charts (via Sheets)
SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def get_credentials(
    *,
    service_account_file: str | Path | None = None,
    client_secrets_file: str | Path | None = None,
    token_file: str | Path | None = None,
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    scopes: list[str] | None = None,
) -> Any:
    """Obtain Google API credentials.

    Priority:
    1. Service account JSON file (server-to-server, no user interaction)
    2. Existing token file (cached OAuth2 token)
    3. refresh_token + client_id + client_secret (direct token refresh)
    4. client_secrets_file (interactive OAuth2 flow — prompts browser)

    Returns a google.oauth2.credentials.Credentials object.
    """
    scopes = scopes or SCOPES

    # 1. Service account
    if service_account_file:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_file(
            str(service_account_file), scopes=scopes,
        )
        log.info("Authenticated via service account: %s", service_account_file)
        return creds

    # 2. Existing token file
    if token_file:
        token_path = Path(token_file)
        if token_path.exists():
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
            if creds.valid:
                log.info("Authenticated via cached token: %s", token_path)
                return creds
            if creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                token_path.write_text(creds.to_json())
                log.info("Refreshed cached token: %s", token_path)
                return creds

    # 3. Direct refresh token
    if refresh_token and client_id and client_secret:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
        )
        creds.refresh(Request())
        log.info("Authenticated via refresh token")
        # Save for future use if token_file specified
        if token_file:
            Path(token_file).write_text(creds.to_json())
        return creds

    # 4. Interactive OAuth2 flow
    if client_secrets_file:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_file), scopes,
        )
        creds = flow.run_local_server(port=0)
        log.info("Authenticated via interactive OAuth2 flow")
        # Save token for future use
        if token_file:
            Path(token_file).write_text(creds.to_json())
        return creds

    raise ValueError(
        "No valid authentication method provided. Supply one of: "
        "service_account_file, token_file, refresh_token+client_id+client_secret, "
        "or client_secrets_file."
    )


def build_slides_service(credentials: Any) -> Any:
    """Build a Google Slides API service object."""
    from googleapiclient.discovery import build

    return build("slides", "v1", credentials=credentials)


def build_sheets_service(credentials: Any) -> Any:
    """Build a Google Sheets API service object."""
    from googleapiclient.discovery import build

    return build("sheets", "v4", credentials=credentials)


def build_drive_service(credentials: Any) -> Any:
    """Build a Google Drive API service object."""
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=credentials)
