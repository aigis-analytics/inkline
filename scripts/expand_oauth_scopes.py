#!/usr/bin/env python3
"""Expand Google OAuth scopes to include Slides, Sheets, and Drive.

This script re-runs the OAuth consent flow with the expanded scopes required
for Inkline's SlideBuilder. It produces a new refresh token that should be
saved to the .env file (GOOGLE_WORKSPACE_REFRESH_TOKEN).

Usage:
    python scripts/expand_oauth_scopes.py --client-secrets /path/to/client_secrets.json

    # Or specify individual credentials:
    python scripts/expand_oauth_scopes.py \
        --client-id YOUR_CLIENT_ID \
        --client-secret YOUR_CLIENT_SECRET

The script will:
1. Open a browser for Google OAuth consent
2. Request expanded scopes (presentations, spreadsheets, drive.file)
3. Print the new refresh token
4. Optionally save to a token file for reuse

Prerequisites:
    pip install google-auth google-auth-oauthlib
"""

import argparse
import json
import sys
from pathlib import Path


SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    # Include existing scopes so the token works for everything
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
    parser = argparse.ArgumentParser(description="Expand Google OAuth scopes for Inkline")
    parser.add_argument("--client-secrets", help="Path to client_secrets.json")
    parser.add_argument("--client-id", help="Google OAuth client ID")
    parser.add_argument("--client-secret", help="Google OAuth client secret")
    parser.add_argument("--token-file", default="token.json", help="Where to save the token")
    parser.add_argument("--port", type=int, default=0, help="Local server port (0=auto)")
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("  pip install google-auth-oauthlib")
        sys.exit(1)

    if args.client_secrets:
        flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    elif args.client_id and args.client_secret:
        client_config = {
            "installed": {
                "client_id": args.client_id,
                "client_secret": args.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    else:
        print("ERROR: Provide --client-secrets OR --client-id + --client-secret")
        sys.exit(1)

    print("\nRequesting scopes:")
    for scope in SCOPES:
        print(f"  - {scope.split('/')[-1]}")
    print("\nOpening browser for consent...")

    creds = flow.run_local_server(port=args.port, open_browser=True)

    # Save token
    token_path = Path(args.token_file)
    token_path.write_text(creds.to_json())
    print(f"\nToken saved to: {token_path}")

    # Print refresh token for .env
    print(f"\n{'='*60}")
    print("Add this to your .env file:")
    print(f"GOOGLE_WORKSPACE_REFRESH_TOKEN={creds.refresh_token}")
    print(f"{'='*60}")

    # Verify
    print(f"\nToken details:")
    print(f"  Client ID: {creds.client_id}")
    print(f"  Scopes: {', '.join(creds.scopes or [])}")
    print(f"  Refresh token: {creds.refresh_token[:20]}...")


if __name__ == "__main__":
    main()
