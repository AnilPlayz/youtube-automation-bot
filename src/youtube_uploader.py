"""YouTube Data API v3 Uploader for automated headless YouTube Shorts publishing."""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from src.config_loader import load_config

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def get_authenticated_service():
    """
    Builds YouTube API service client from environment credentials / refresh token.
    Supports GitHub Actions headless authentication.
    """
    client_id = (os.getenv("YOUTUBE_CLIENT_ID") or "").strip().strip('"').strip("'")
    client_secret = (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip().strip('"').strip("'")
    refresh_token = (os.getenv("YOUTUBE_REFRESH_TOKEN") or "").strip().strip('"').strip("'")

    if not (client_id and client_secret and refresh_token):
        print("[YouTube Uploader Warning] Missing YouTube OAuth credentials (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN).")
        return None

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    if not credentials.valid:
        credentials.refresh(Request())

    return build("youtube", "v3", credentials=credentials)

def upload_short_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy_status: Optional[str] = None
) -> Optional[str]:
    """
    Uploads MP4 video to YouTube as a Short.
    Returns the YouTube video ID if successful.
    """
    config = load_config()
    yt_cfg = config.get("youtube", {})
    privacy = privacy_status or yt_cfg.get("privacy_status", "public")
    category_id = yt_cfg.get("category_id", "20")  # 20 = Gaming

    # Ensure title has #shorts
    if "#shorts" not in title.lower() and "#short" not in title.lower():
        title = f"{title} #shorts"

    # Ensure description has #shorts
    if "#shorts" not in description.lower():
        description = f"{description}\n\n#shorts #minecraft #gaming"

    merged_tags = list(set((tags or []) + yt_cfg.get("default_tags", ["minecraft", "shorts"])))

    service = get_authenticated_service()
    if not service:
        print("[YouTube Uploader] Skipping upload: No valid YouTube API credentials found in environment.")
        return None

    print(f"[YouTube Uploader] Uploading '{title}' ({privacy})...")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": merged_tags[:50],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 4,
        resumable=True,
        mimetype="video/mp4"
    )

    request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retry_count = 0
    max_retries = 5

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"[YouTube Uploader] Upload progress: {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                retry_count += 1
                wait_time = 2 ** retry_count
                print(f"[YouTube Uploader] Temporary server error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e

    if response and "id" in response:
        video_id = response["id"]
        short_url = f"https://youtube.com/shorts/{video_id}"
        print(f"[YouTube Uploader] Successfully published Short: {short_url}")
        return video_id

    return None

if __name__ == "__main__":
    service = get_authenticated_service()
    if service:
        print("YouTube API authentication is valid!")
    else:
        print("Please configure YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN in .env")
