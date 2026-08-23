"""Interactive helper to obtain YouTube OAuth2 Refresh Token for GitHub Actions.
Run this locally once to get your YOUTUBE_REFRESH_TOKEN.
"""

import json
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def generate_refresh_token():
    print("=" * 60)
    print("   YOUTUBE OAUTH2 REFRESH TOKEN GENERATOR")
    print("=" * 60)
    print("This script will help you generate the credentials needed for GitHub Actions.")
    print("\nPrerequisites:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com")
    print("2. Create a project and enable 'YouTube Data API v3'.")
    print("3. Configure OAuth Consent Screen (User Type: External, Publishing status: Testing or In production).")
    print("4. Create OAuth 2.0 Client ID (Application Type: Desktop App).")
    print("5. Download client_secret.json or note your Client ID and Client Secret.")
    print("-" * 60)

    client_secret_file = Path("client_secret.json")
    
    if client_secret_file.exists():
        print(f"Found {client_secret_file.name}! Starting local authorization server...")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
    else:
        client_id = input("\nEnter your OAuth Client ID: ").strip()
        client_secret = input("Enter your OAuth Client Secret: ").strip()
        
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")

    print("\n" + "=" * 60)
    print(" AUTHORIZATION SUCCESSFUL! SAVE THESE TO YOUR GITHUB SECRETS:")
    print("=" * 60)
    print(f"YOUTUBE_CLIENT_ID={creds.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={creds.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 60)
    print("\nAdd these 3 variables to your GitHub Repo -> Settings -> Secrets and variables -> Actions")

if __name__ == "__main__":
    generate_refresh_token()
