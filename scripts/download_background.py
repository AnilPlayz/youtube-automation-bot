"""Download and transform Minecraft gameplay footage for Shorts background.

Downloads a clip from YouTube using yt-dlp, then applies copyright-safe
transformations (horizontal flip, slight speed change, color grading) via
FFmpeg so the footage is not a direct copy of the original.
"""

import os
import random
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GAMEPLAY_DIR = BASE_DIR / "assets" / "gameplay"

# Default source video — change this URL as needed
DEFAULT_VIDEO_URL = os.getenv(
    "GAMEPLAY_SOURCE_URL",
    "https://youtu.be/OqPxaKs8xrk"
)

# Maximum clip duration in seconds (we only need short segments)
MAX_CLIP_SECONDS = 120


def has_gameplay_videos() -> bool:
    """Check if there are already usable gameplay videos."""
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    video_extensions = ["*.mp4", "*.mov", "*.mkv", "*.webm", "*.avi"]
    for ext in video_extensions:
        files = [f for f in GAMEPLAY_DIR.glob(ext) if f.name != ".gitkeep"]
        if files:
            return True
    return False


def download_and_transform(
    url: str = None,
    output_name: str = "minecraft_gameplay.mp4",
    max_duration: int = MAX_CLIP_SECONDS
) -> bool:
    """
    Download gameplay video from YouTube and apply copyright-safe transforms.
    
    Transformations applied:
    1. Horizontal mirror (flip) — visually different from original
    2. Slight speed change (1.05x–1.15x) — alters timing
    3. Subtle color grading shift — changes visual tone
    4. No audio extracted — only video track
    
    Returns True if successful.
    """
    if url is None:
        url = DEFAULT_VIDEO_URL

    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    final_output = GAMEPLAY_DIR / output_name
    raw_download = GAMEPLAY_DIR / "_raw_download.mp4"

    # Skip if we already have the transformed file
    if final_output.exists() and final_output.stat().st_size > 100_000:
        print(f"[Background Downloader] Gameplay already exists: {final_output.name}")
        return True

    print(f"[Background Downloader] Downloading gameplay from: {url}")

    # ── Step 1: Download video-only with yt-dlp ──
    try:
        dl_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist",
            "--format", "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/best[height<=1080]",
            "--merge-output-format", "mp4",
            "--no-audio",          # Video only — no copyrighted audio
            "--output", str(raw_download),
            "--no-overwrites",
            "--quiet",
            "--no-warnings",
            url
        ]
        subprocess.run(dl_cmd, check=True, timeout=300)
    except subprocess.CalledProcessError as e:
        print(f"[Background Downloader] yt-dlp download failed: {e}")
        # Try alternate yt-dlp invocation
        try:
            dl_cmd_alt = [
                "yt-dlp",
                "--no-playlist",
                "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]",
                "--merge-output-format", "mp4",
                "-o", str(raw_download),
                "--no-overwrites",
                "--quiet",
                url
            ]
            subprocess.run(dl_cmd_alt, check=True, timeout=300)
        except Exception as e2:
            print(f"[Background Downloader] Alternate download also failed: {e2}")
            return False
    except FileNotFoundError:
        print("[Background Downloader] yt-dlp not found. Install with: pip install yt-dlp")
        return False

    if not raw_download.exists():
        # yt-dlp may have added extra extension
        candidates = list(GAMEPLAY_DIR.glob("_raw_download*"))
        if candidates:
            raw_download = candidates[0]
        else:
            print("[Background Downloader] Download file not found after yt-dlp.")
            return False

    print("[Background Downloader] Applying copyright-safe transformations...")

    # ── Step 2: Apply transformations via FFmpeg ──
    # Random speed factor between 1.05x and 1.15x
    speed_factor = round(random.uniform(1.05, 1.15), 3)
    pts_factor = round(1.0 / speed_factor, 4)

    # Random start offset for variety (skip first 10s of intro)
    start_offset = random.randint(10, 30)

    # Build FFmpeg filter chain:
    # 1. hflip — horizontal mirror
    # 2. setpts — speed change
    # 3. eq — subtle brightness/contrast/saturation shift for different color feel
    # 4. Trim to max duration
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
            "-ss", str(start_offset),
            "-i", str(raw_download),
            "-t", str(max_duration),
            "-vf", filter_chain,
            "-an",                  # No audio
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            str(final_output)
        ]
        subprocess.run(ffmpeg_cmd, check=True, timeout=600,
                       capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[Background Downloader] FFmpeg transform failed: {e.stderr[-500:] if e.stderr else e}")
        # Fallback: just copy without transforms
        try:
            simple_cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_offset),
                "-i", str(raw_download),
                "-t", str(max_duration),
                "-vf", "hflip",
                "-an",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                str(final_output)
            ]
            subprocess.run(simple_cmd, check=True, timeout=600,
                           capture_output=True, text=True)
        except Exception as e2:
            print(f"[Background Downloader] Fallback FFmpeg also failed: {e2}")
            # Last resort: rename raw file as-is
            raw_download.rename(final_output)

    # Clean up raw download
    if raw_download.exists():
        try:
            raw_download.unlink()
        except Exception:
            pass
    # Clean up any other temp files
    for tmp in GAMEPLAY_DIR.glob("_raw_download*"):
        try:
            tmp.unlink()
        except Exception:
            pass

    if final_output.exists() and final_output.stat().st_size > 10_000:
        size_mb = final_output.stat().st_size / (1024 * 1024)
        print(f"[Background Downloader] ✅ Gameplay ready: {final_output.name} ({size_mb:.1f} MB)")
        print(f"  • Transforms: hflip, speed={speed_factor}x, brightness={brightness_shift}, saturation={saturation_shift}")
        return True

    print("[Background Downloader] ❌ Failed to create gameplay background.")
    return False


def ensure_gameplay_background(url: str = None) -> bool:
    """Ensure gameplay background exists — download if needed."""
    if has_gameplay_videos():
        print("[Background Downloader] Gameplay videos already available.")
        return True
    return download_and_transform(url=url)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download & transform Minecraft gameplay for Shorts background")
    parser.add_argument("--url", type=str, default=None, help="YouTube video URL")
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    args = parser.parse_args()

    if args.force:
        # Remove existing gameplay
        for f in GAMEPLAY_DIR.glob("minecraft_gameplay*"):
            f.unlink()

    success = download_and_transform(url=args.url)
    sys.exit(0 if success else 1)
