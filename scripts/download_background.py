"""Download gaming/Minecraft-style gameplay footage for Shorts background.

Uses multiple strategies:
1. Try yt-dlp for YouTube URLs (works locally, blocked on CI)
2. Search Pexels API for free gaming/pixel footage  
3. Download from reliable direct URLs as fallback
4. Apply copyright-safe transformations via FFmpeg
"""

import io
import os
import random
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
GAMEPLAY_DIR = BASE_DIR / "assets" / "gameplay"

MAX_CLIP_SECONDS = 120


def has_gameplay_videos() -> bool:
    """Check if there are already usable gameplay videos."""
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    video_extensions = ["*.mp4", "*.mov", "*.mkv", "*.webm", "*.avi"]
    for ext in video_extensions:
        files = [f for f in GAMEPLAY_DIR.glob(ext)
                 if f.name not in (".gitkeep", "_raw_download.mp4")
                 and not f.name.startswith("_raw")]
        if files:
            return True
    return False


def download_from_pexels(output_path: Path, query: str = "minecraft game") -> bool:
    """Search Pexels for free gaming videos and download one."""
    import requests

    # Try multiple search terms
    search_queries = [query, "pixel game", "gaming screen", "arcade game retro",
                      "abstract dark particles", "neon particles dark"]

    for search_q in search_queries:
        try:
            # Pexels free API - no key needed for basic search page scraping
            # Use their video search page to find direct URLs
            search_url = f"https://www.pexels.com/search/videos/{search_q.replace(' ', '-')}/"
            resp = requests.get(search_url, timeout=15,
                              headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if resp.status_code != 200:
                continue

            # Extract video URLs from the page
            import re
            # Look for .mp4 URLs in the page source
            mp4_urls = re.findall(r'https://[^"\']*\.mp4[^"\']*', resp.text)
            # Filter for reasonable sized videos
            video_urls = [u for u in mp4_urls if 'video' in u.lower() and len(u) < 300]

            if not video_urls:
                continue

            # Try to download the first available video
            random.shuffle(video_urls)
            for video_url in video_urls[:5]:
                try:
                    print(f"[Background Downloader] Trying Pexels video: {video_url[:80]}...")
                    vid_resp = requests.get(video_url, stream=True, timeout=60,
                                           headers={"User-Agent": "Mozilla/5.0"})
                    if vid_resp.status_code == 200:
                        total = 0
                        with open(output_path, "wb") as f:
                            for chunk in vid_resp.iter_content(chunk_size=1024 * 1024):
                                f.write(chunk)
                                total += len(chunk)
                        if total > 500_000:  # At least 500KB
                            print(f"[Background Downloader] Downloaded {total / (1024*1024):.1f} MB from Pexels")
                            return True
                        else:
                            output_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"[Background Downloader] Pexels video download failed: {e}")
                    continue
        except Exception as e:
            print(f"[Background Downloader] Pexels search '{search_q}' failed: {e}")
            continue

    return False


def download_from_direct_urls(output_path: Path) -> bool:
    """Download from known working direct video URLs."""
    import requests

    # These are stable, public domain / CC0 video sources
    # Using archive.org which has stable URLs
    direct_sources = [
        # Google sample videos (very stable, public domain)
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        # W3Schools test video (Big Buck Bunny clip, reliable)
        "https://www.w3schools.com/html/mov_bbb.mp4",
    ]

    for url in direct_sources:
        try:
            print(f"[Background Downloader] Trying direct URL: {url[:60]}...")
            resp = requests.get(url, stream=True, timeout=60,
                              headers={"User-Agent": "Mozilla/5.0"},
                              allow_redirects=True)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "video" in content_type or url.endswith(".mp4"):
                    total = 0
                    with open(output_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):
                            f.write(chunk)
                            total += len(chunk)
                    if total > 100_000:
                        print(f"[Background Downloader] Downloaded {total / (1024*1024):.1f} MB")
                        return True
                    else:
                        output_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"[Background Downloader] Direct download failed for {url[:50]}: {e}")
            continue

    return False


# FFmpeg filter chains for each theme's procedural video
THEME_FFMPEG_FILTERS = {
    "nether": {
        "base_color": "0x1a0500",
        "filter": (
            "geq="
            "r='clip(80+60*sin(2*PI*T/3+X/80)+40*sin(2*PI*T/5+Y/150),40,220)':"
            "g='clip(15+10*sin(2*PI*T/4+Y/200)+8*sin(2*PI*T/7+X/120),0,50)':"
            "b='clip(5+5*sin(2*PI*T/6+X/150+Y/250),0,20)'"
        ),
        "extra_filters": "eq=brightness=0.05:saturation=1.3",
    },
    "end": {
        "base_color": "0x0a0020",
        "filter": (
            "geq="
            "r='clip(30+20*sin(2*PI*T/6+X/120)+15*sin(2*PI*T/9+Y/180),5,80)':"
            "g='clip(8+8*sin(2*PI*T/5+Y/200)+5*sin(2*PI*T/8+X/150),0,30)':"
            "b='clip(60+40*sin(2*PI*T/4+X/100+Y/160)+25*sin(2*PI*T/7),20,120)'"
        ),
        "extra_filters": "eq=brightness=-0.05:saturation=1.2",
    },
    "ocean": {
        "base_color": "0x001a3d",
        "filter": (
            "geq="
            "r='clip(10+8*sin(2*PI*T/5+X/150+Y/200)+5*sin(2*PI*T/8+X/100),0,40)':"
            "g='clip(30+20*sin(2*PI*T/4+Y/120)+15*sin(2*PI*T/6+X/180),10,80)':"
            "b='clip(80+50*sin(2*PI*T/3+X/90+Y/140)+30*sin(2*PI*T/7),30,160)'"
        ),
        "extra_filters": "eq=brightness=0.02:saturation=1.1",
    },
    "cave": {
        "base_color": "0x0a0c14",
        "filter": (
            "geq="
            "r='clip(15+10*sin(2*PI*T/8+X/200)+8*sin(2*PI*T/12+Y/250),5,40)':"
            "g='clip(20+15*sin(2*PI*T/6+Y/180)+10*sin(2*PI*T/10+X/160),5,50)':"
            "b='clip(40+30*sin(2*PI*T/5+X/120+Y/200)+20*sin(2*PI*T/9),10,80)'"
        ),
        "extra_filters": "eq=brightness=-0.08:saturation=0.9",
    },
    "overworld": {
        "base_color": "0x0a2d0a",
        "filter": (
            "geq="
            "r='clip(20+15*sin(2*PI*T/6+X/130)+10*sin(2*PI*T/8+Y/200),5,60)':"
            "g='clip(50+35*sin(2*PI*T/4+Y/100)+25*sin(2*PI*T/7+X/150),15,120)':"
            "b='clip(15+10*sin(2*PI*T/7+X/180+Y/220)+8*sin(2*PI*T/10),5,40)'"
        ),
        "extra_filters": "eq=brightness=0.03:saturation=1.2",
    },
    "redstone": {
        "base_color": "0x140000",
        "filter": (
            "geq="
            "r='clip(60+45*sin(2*PI*T/4+X/100)+30*sin(2*PI*T/6+Y/140),20,160)':"
            "g='clip(5+5*sin(2*PI*T/8+Y/200)+3*sin(2*PI*T/12+X/180),0,20)':"
            "b='clip(8+6*sin(2*PI*T/7+X/160+Y/200)+4*sin(2*PI*T/10),0,25)'"
        ),
        "extra_filters": "eq=brightness=0.02:saturation=1.4",
    },
    "magic": {
        "base_color": "0x0f0530",
        "filter": (
            "geq="
            "r='clip(40+30*sin(2*PI*T/5+X/110)+20*sin(2*PI*T/7+Y/170),10,100)':"
            "g='clip(15+10*sin(2*PI*T/6+Y/190)+8*sin(2*PI*T/9+X/140),0,40)':"
            "b='clip(70+50*sin(2*PI*T/4+X/90+Y/130)+30*sin(2*PI*T/8),20,140)'"
        ),
        "extra_filters": "eq=brightness=0.03:saturation=1.3",
    },
    "mob": {
        "base_color": "0x140508",
        "filter": (
            "geq="
            "r='clip(50+35*sin(2*PI*T/5+X/100)+25*sin(2*PI*T/7+Y/160),15,120)':"
            "g='clip(8+6*sin(2*PI*T/8+Y/220)+4*sin(2*PI*T/11+X/180),0,25)':"
            "b='clip(12+8*sin(2*PI*T/7+X/150+Y/200)+5*sin(2*PI*T/10),0,30)'"
        ),
        "extra_filters": "eq=brightness=-0.05:saturation=1.2",
    },
}


def generate_themed_procedural_video(output_path: Path, theme: str, duration: int = 90) -> bool:
    """Generate a themed animated background video using FFmpeg geq filters."""
    if theme not in THEME_FFMPEG_FILTERS:
        theme = "overworld"

    cfg = THEME_FFMPEG_FILTERS[theme]
    base_color = cfg["base_color"]
    vf_chain = cfg["filter"]

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={base_color}:s=1080x1920:d={duration}",
            "-vf", vf_chain,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "26",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-an",
            str(output_path),
        ]
        print(f"[Background Downloader] Generating {theme} themed procedural background...")
        subprocess.run(cmd, check=True, timeout=300, capture_output=True, text=True)

        if output_path.exists() and output_path.stat().st_size > 50_000:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"[Background Downloader] ✅ {theme} procedural background: {size_mb:.1f} MB")
            return True

        print(f"[Background Downloader] ❌ {theme} procedural video too small")
        output_path.unlink(missing_ok=True)
        return False
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"[Background Downloader] ❌ {theme} procedural generation failed: {e}")
        output_path.unlink(missing_ok=True)
        return False


def generate_procedural_video(output_path: Path, duration: int = 60) -> bool:
    """Generate a dark animated background video using FFmpeg as ultimate fallback."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0a0a2a:s=1080x1920:d={duration}",
            "-vf", (
                f"geq="
                f"r='clip(30+20*sin(2*PI*T/5+X/100)+15*sin(2*PI*T/7+Y/200),5,60)':"
                f"g='clip(10+10*sin(2*PI*T/3+Y/150)+8*sin(2*PI*T/6+X/180),0,30)':"
                f"b='clip(40+30*sin(2*PI*T/4+X/80+Y/120)+20*sin(2*PI*T/8),15,80)'"
            ),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-an",
            str(output_path)
        ]
        print("[Background Downloader] Generating procedural dark gaming background...")
        subprocess.run(cmd, check=True, timeout=300, capture_output=True, text=True)
        return output_path.exists() and output_path.stat().st_size > 10_000
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"[Background Downloader] Procedural generation failed: {e}")
        return False


def try_yt_dlp_download(url: str, output_path: Path) -> bool:
    """Try downloading from YouTube using yt-dlp (may fail on CI)."""
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
        print(f"[Background Downloader] Transforms: hflip, speed={speed_factor}x, "
              f"brightness={brightness_shift}, saturation={saturation_shift}")
        subprocess.run(ffmpeg_cmd, check=True, timeout=600,
                       capture_output=True, text=True)
        return output_path.exists() and output_path.stat().st_size > 10_000
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"[Background Downloader] FFmpeg transform failed ({type(e).__name__}), trying simple copy...")
        try:
            simple_cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-t", str(max_duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-an", "-c:v", "libx264", "-preset", "ultrafast",
                str(output_path)
            ]
            subprocess.run(simple_cmd, check=True, timeout=600,
                           capture_output=True, text=True)
            return output_path.exists() and output_path.stat().st_size > 10_000
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e2:
            print(f"[Background Downloader] FFmpeg not available: {e2}")
            # Fallback: just copy the file as-is
            try:
                import shutil
                shutil.copy2(str(input_path), str(output_path))
                return output_path.exists() and output_path.stat().st_size > 10_000
            except Exception:
                return False


def download_and_transform(url: str = None,
                           output_name: str = "minecraft_gameplay.mp4") -> bool:
    """
    Download gameplay video and apply copyright-safe transforms.

    Strategy order:
    1. yt-dlp (if YouTube URL provided — works locally, may fail on CI)
    2. Pexels free video search
    3. Direct URL fallback
    4. FFmpeg procedural generation (guaranteed to work)
    """
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    final_output = GAMEPLAY_DIR / output_name
    raw_download = GAMEPLAY_DIR / "_raw_download.mp4"

    # Skip if already exists
    if final_output.exists() and final_output.stat().st_size > 100_000:
        print(f"[Background Downloader] Gameplay already exists: {final_output.name}")
        return True

    # Clean up previous attempts
    for tmp in GAMEPLAY_DIR.glob("_raw_*"):
        tmp.unlink(missing_ok=True)

    downloaded = False

    # Strategy 1: yt-dlp
    if url and ("youtube.com" in url or "youtu.be" in url):
        print(f"[Background Downloader] Trying YouTube: {url}")
        downloaded = try_yt_dlp_download(url, raw_download)

    # Strategy 2: Pexels search
    if not downloaded:
        print("[Background Downloader] Searching Pexels for gaming footage...")
        downloaded = download_from_pexels(raw_download)

    # Strategy 3: Direct URLs
    if not downloaded:
        print("[Background Downloader] Trying direct download sources...")
        downloaded = download_from_direct_urls(raw_download)

    # Strategy 4: Generate with FFmpeg (guaranteed fallback)
    if not downloaded:
        print("[Background Downloader] All downloads failed. Generating procedural background...")
        if generate_procedural_video(final_output, duration=90):
            print(f"[Background Downloader] ✅ Procedural gameplay background generated")
            return True
        return False

    # Apply transforms to downloaded video
    print("[Background Downloader] Applying copyright-safe transformations...")
    success = transform_video(raw_download, final_output)

    # Clean up
    for tmp in GAMEPLAY_DIR.glob("_raw_*"):
        tmp.unlink(missing_ok=True)

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


# Themed gameplay search queries for Pexels
THEME_SEARCH_QUERIES = {
    "nether": ["fire lava dark", "volcano eruption", "hell fire flames"],
    "end": ["dark void space", "purple portal", "dark dimension"],
    "ocean": ["underwater ocean deep", "ocean waves underwater", "coral reef fish"],
    "cave": ["dark cave tunnel", "underground mine", "crystal cave dark"],
    "overworld": ["minecraft game", "pixel game green", "forest nature game"],
    "redstone": ["circuit board technology", "gears machine mechanical", "neon tech abstract"],
    "magic": ["magic spell particles", "enchanted glowing", "mystical light particles"],
    "mob": ["monster creature dark", "zombie horror dark", "skeleton dark gaming"],
}


def download_themed_gameplay(theme: str = None) -> bool:
    """
    Download or generate theme-specific gameplay videos.
    Strategy: FFmpeg procedural generation (reliable) → Pexels search → direct URL fallback.
    Returns True if at least one video was obtained.
    """
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)

    themes_to_download = [theme] if theme else list(THEME_SEARCH_QUERIES.keys())
    downloaded_any = False

    for t in themes_to_download:
        output_name = f"{t}_gameplay.mp4"
        final_output = GAMEPLAY_DIR / output_name

        # Skip if already exists and valid
        if final_output.exists() and final_output.stat().st_size > 50_000:
            print(f"[Background Downloader] {t} gameplay already exists: {output_name}")
            downloaded_any = True
            continue

        success = False

        # Strategy 1: Generate themed procedural video (reliable, no network needed)
        print(f"[Background Downloader] Creating {t} themed gameplay...")
        success = generate_themed_procedural_video(final_output, t, duration=90)

        if not success:
            # Strategy 2: Pexels search (may fail on CI)
            queries = THEME_SEARCH_QUERIES.get(t, ["minecraft game"])
            raw_download = GAMEPLAY_DIR / f"_raw_{t}.mp4"
            for query in queries:
                print(f"[Background Downloader] Searching Pexels for {t}: '{query}'...")
                success = download_from_pexels(raw_download, query=query)
                if success:
                    break
            if success:
                transform_video(raw_download, final_output)
                raw_download.unlink(missing_ok=True)
                success = final_output.exists() and final_output.stat().st_size > 10_000

        if not success:
            # Strategy 3: Direct URL fallback
            raw_download = GAMEPLAY_DIR / f"_raw_{t}.mp4"
            success = download_from_direct_urls(raw_download)
            if success:
                transform_video(raw_download, final_output)
                raw_download.unlink(missing_ok=True)
                success = final_output.exists() and final_output.stat().st_size > 10_000

        if success and final_output.exists() and final_output.stat().st_size > 10_000:
            size_mb = final_output.stat().st_size / (1024 * 1024)
            print(f"[Background Downloader] ✅ {t} themed gameplay ready: {output_name} ({size_mb:.1f} MB)")
            downloaded_any = True
        else:
            print(f"[Background Downloader] ❌ Failed to create {t} themed gameplay")

        # Cleanup any raw downloads
        for tmp in GAMEPLAY_DIR.glob(f"_raw_{t}*"):
            tmp.unlink(missing_ok=True)

    return downloaded_any


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Download & transform gameplay for Shorts background")
    parser.add_argument("--url", type=str, default=None, help="Video URL")
    parser.add_argument("--force", action="store_true", help="Re-download")
    parser.add_argument("--theme", type=str, default=None,
                        choices=list(THEME_SEARCH_QUERIES.keys()),
                        help="Download themed gameplay for specific theme")
    parser.add_argument("--all-themes", action="store_true",
                        help="Download gameplay for all themes")
    args = parser.parse_args()

    if args.force:
        for f in GAMEPLAY_DIR.glob("minecraft_gameplay*"):
            f.unlink()
        for f in GAMEPLAY_DIR.glob("*_gameplay.mp4"):
            f.unlink()

    if args.all_themes:
        success = download_themed_gameplay()
    elif args.theme:
        success = download_themed_gameplay(theme=args.theme)
    else:
        success = download_and_transform(url=args.url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Download & transform gameplay for Shorts background")
    parser.add_argument("--url", type=str, default=None, help="Video URL")
    parser.add_argument("--force", action="store_true", help="Re-download")
    args = parser.parse_args()

    if args.force:
        for f in GAMEPLAY_DIR.glob("minecraft_gameplay*"):
            f.unlink()

    success = download_and_transform(url=args.url)
    sys.exit(0 if success else 1)
