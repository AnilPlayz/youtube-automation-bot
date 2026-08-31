"""Download Minecraft gameplay footage for Shorts background.

Uses direct download URLs from royalty-free/Creative Commons sources
since YouTube blocks headless downloads on CI servers.
Applies copyright-safe transformations via FFmpeg.
"""

import os
import random
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GAMEPLAY_DIR = BASE_DIR / "assets" / "gameplay"

# Direct download URLs for Minecraft-style gameplay (royalty-free / CC0)
# These are direct video file URLs that work without authentication
GAMEPLAY_SOURCES = [
    # Pixabay free stock Minecraft-style game footage (CC0 / royalty-free)
    "https://cdn.pixabay.com/video/2022/11/07/138226-768988754_large.mp4",
    "https://cdn.pixabay.com/video/2023/04/12/158779-817083291_large.mp4",
    "https://cdn.pixabay.com/video/2024/02/05/199410-910102654_large.mp4",
]

MAX_CLIP_SECONDS = 120


def has_gameplay_videos() -> bool:
    """Check if there are already usable gameplay videos."""
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    video_extensions = ["*.mp4", "*.mov", "*.mkv", "*.webm", "*.avi"]
    for ext in video_extensions:
        files = [f for f in GAMEPLAY_DIR.glob(ext)
                 if f.name not in (".gitkeep", "_raw_download.mp4")]
        if files:
            return True
    return False


def download_direct_video(url: str, output_path: Path) -> bool:
    """Download video from a direct URL using requests or curl."""
    import requests
    try:
        print(f"[Background Downloader] Downloading from: {url}")
        resp = requests.get(url, stream=True, timeout=120,
                           headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        total = 0
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)

        if total > 100_000:
            size_mb = total / (1024 * 1024)
            print(f"[Background Downloader] Downloaded {size_mb:.1f} MB")
            return True
        else:
            print(f"[Background Downloader] Download too small ({total} bytes)")
            if output_path.exists():
                output_path.unlink()
            return False

    except Exception as e:
        print(f"[Background Downloader] Download failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def try_yt_dlp_download(url: str, output_path: Path) -> bool:
    """Try downloading from YouTube using yt-dlp (may fail on CI due to bot detection)."""
    try:
        dl_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist",
            "--format", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]",
            "--merge-output-format", "mp4",
            "--output", str(output_path),
            "--no-overwrites",
            "--quiet",
            "--no-warnings",
            url
        ]
        subprocess.run(dl_cmd, check=True, timeout=300,
                       capture_output=True, text=True)
        return output_path.exists() and output_path.stat().st_size > 100_000
    except Exception as e:
        print(f"[Background Downloader] yt-dlp failed: {e}")
        return False


def transform_video(input_path: Path, output_path: Path,
                    max_duration: int = MAX_CLIP_SECONDS) -> bool:
    """Apply copyright-safe transforms via FFmpeg."""
    speed_factor = round(random.uniform(1.05, 1.15), 3)
    pts_factor = round(1.0 / speed_factor, 4)
    brightness_shift = round(random.uniform(-0.05, 0.05), 3)
    saturation_shift = round(random.uniform(0.85, 1.15), 2)

    filter_chain = (
        f"hflip,"
        f"setpts={pts_factor}*PTS,"
        f"eq=brightness={brightness_shift}:saturation={saturation_shift},"
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920"
    )

    try:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-t", str(max_duration),
            "-vf", filter_chain,
            "-an",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            str(output_path)
        ]
        print(f"[Background Downloader] Applying transforms: hflip, speed={speed_factor}x, "
              f"brightness={brightness_shift}, saturation={saturation_shift}")
        result = subprocess.run(ffmpeg_cmd, check=True, timeout=600,
                               capture_output=True, text=True)
        return output_path.exists() and output_path.stat().st_size > 10_000
    except subprocess.CalledProcessError as e:
        print(f"[Background Downloader] FFmpeg transform failed: {e.stderr[-300:] if e.stderr else e}")
        # Fallback: simple copy with just hflip
        try:
            simple_cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-t", str(max_duration),
                "-vf", "hflip,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-an",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                str(output_path)
            ]
            subprocess.run(simple_cmd, check=True, timeout=600,
                           capture_output=True, text=True)
            return output_path.exists() and output_path.stat().st_size > 10_000
        except Exception as e2:
            print(f"[Background Downloader] Fallback FFmpeg also failed: {e2}")
            return False


def download_and_transform(
    url: str = None,
    output_name: str = "minecraft_gameplay.mp4",
) -> bool:
    """
    Download gameplay video and apply copyright-safe transforms.

    Strategy:
    1. If a YouTube URL is provided, try yt-dlp first
    2. Fall back to direct download from royalty-free sources
    3. Apply transforms (hflip, speed, color) via FFmpeg

    Returns True if successful.
    """
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    final_output = GAMEPLAY_DIR / output_name
    raw_download = GAMEPLAY_DIR / "_raw_download.mp4"

    # Skip if we already have the transformed file
    if final_output.exists() and final_output.stat().st_size > 100_000:
        print(f"[Background Downloader] Gameplay already exists: {final_output.name}")
        return True

    # Clean up any previous failed downloads
    if raw_download.exists():
        raw_download.unlink()

    downloaded = False

    # Strategy 1: Try yt-dlp if a YouTube URL is provided
    if url and ("youtube.com" in url or "youtu.be" in url):
        print(f"[Background Downloader] Trying YouTube download: {url}")
        downloaded = try_yt_dlp_download(url, raw_download)

    # Strategy 2: Direct download from royalty-free sources
    if not downloaded:
        print("[Background Downloader] Using royalty-free gameplay source...")
        random.shuffle(GAMEPLAY_SOURCES)
        for source_url in GAMEPLAY_SOURCES:
            downloaded = download_direct_video(source_url, raw_download)
            if downloaded:
                break

    if not downloaded or not raw_download.exists():
        print("[Background Downloader] ❌ All download attempts failed.")
        return False

    # Apply transforms
    print("[Background Downloader] Applying copyright-safe transformations...")
    success = transform_video(raw_download, final_output)

    # Clean up raw download
    for tmp in GAMEPLAY_DIR.glob("_raw_*"):
        try:
            tmp.unlink()
        except Exception:
            pass

    if success:
        size_mb = final_output.stat().st_size / (1024 * 1024)
        print(f"[Background Downloader] ✅ Gameplay ready: {final_output.name} ({size_mb:.1f} MB)")
        return True

    print("[Background Downloader] ❌ Failed to create gameplay background.")
    return False


def ensure_gameplay_background(url: str = None) -> bool:
    """Ensure gameplay background exists — download if needed."""
    if has_gameplay_videos():
        print("[Background Downloader] Gameplay videos already available.")
        return True

    if url is None:
        url = os.getenv("GAMEPLAY_SOURCE_URL", "")

    return download_and_transform(url=url)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Download & transform gameplay for Shorts background")
    parser.add_argument("--url", type=str, default=None,
                       help="YouTube or direct video URL")
    parser.add_argument("--force", action="store_true",
                       help="Re-download even if file exists")
    args = parser.parse_args()

    if args.force:
        for f in GAMEPLAY_DIR.glob("minecraft_gameplay*"):
            f.unlink()

    success = download_and_transform(url=args.url)
    sys.exit(0 if success else 1)
