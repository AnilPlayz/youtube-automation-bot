"""Master Pipeline Orchestrator for Minecraft Facts YouTube Shorts Automation."""

import argparse
import sys
import time
from pathlib import Path

# Fix Windows console encoding for emoji output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config_loader import load_config, BASE_DIR
from src.script_generator import get_unique_script
from src.tts_engine import generate_voiceover
from src.video_composer import create_full_short_video
from src.youtube_uploader import upload_short_to_youtube
from scripts.download_background import ensure_gameplay_background, download_themed_gameplay, GAMEPLAY_DIR

OUTPUT_DIR = BASE_DIR / "output"

def run_pipeline(
    dry_run: bool = False,
    force_topic: str = None,
    custom_username: str = None,
    privacy: str = None
):
    start_time = time.time()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())

    print("=" * 65)
    print(" 🚀 STARTING AI MINECRAFT FACTS SHORTS AUTOMATION PIPELINE")
    print("=" * 65)

    # 1. Generate Unique Script (first, so we know the theme)
    print("\n[Step 1/5] Generating unique viral Minecraft fact script...")
    script_data = get_unique_script(force_topic=force_topic)
    topic_theme = script_data.get("topic_theme", "overworld")
    print(f"  • Topic:       {script_data['topic']}")
    print(f"  • Title:       {script_data['title']}")
    print(f"  • Theme:       {topic_theme}")
    print(f"  • Script Words: {len(script_data['voiceover_script'].split())} words")

    # 2. Ensure themed gameplay background footage matches the topic
    print(f"\n[Step 2/5] Ensuring {topic_theme}-themed gameplay background...")
    bg_ready = False
    theme_video = GAMEPLAY_DIR / f"{topic_theme}_gameplay.mp4"
    if theme_video.exists() and theme_video.stat().st_size > 50_000:
        print(f"  • ✅ {topic_theme} gameplay already available")
        bg_ready = True
    else:
        bg_ready = download_themed_gameplay(theme=topic_theme)
    if not bg_ready:
        bg_ready = ensure_gameplay_background()
    if bg_ready:
        print(f"  • ✅ Gameplay background ready ({topic_theme})")
    else:
        print(f"  • ⚠️ No gameplay footage available — will use animated backdrop")

    # 3. Generate Voiceover & Subtitles
    print("\n[Step 3/5] Synthesizing neural voiceover and extracting word timestamps...")
    audio_path = str(OUTPUT_DIR / f"voiceover_{timestamp}.mp3")
    audio_file, sub_chunks = generate_voiceover(
        script_text=script_data["voiceover_script"],
        output_audio_path=audio_path
    )
    print(f"  • Voiceover saved: {audio_file}")
    print(f"  • Subtitle chunks: {len(sub_chunks)} phrases synced")

    # 4. Assemble Video
    print(f"\n[Step 4/5] Compositing 9:16 Short ({topic_theme} theme: gameplay + subtitles + watermark + player avatar)...")
    video_output_path = str(OUTPUT_DIR / f"minecraft_short_{timestamp}.mp4")
    final_video = create_full_short_video(
        voiceover_path=audio_file,
        subtitle_chunks=sub_chunks,
        output_mp4_path=video_output_path,
        custom_username=custom_username,
        topic_theme=topic_theme
    )
    print(f"  • Rendered Video: {final_video}")

    # 5. Upload to YouTube
    upload_success = False
    if dry_run:
        print("\n[Step 5/5] ⚠️ DRY-RUN MODE: Skipping YouTube upload.")
        print(f"  • Video file ready at: {final_video}")
        video_id = "DRY_RUN_LOCAL"
        upload_success = True
    else:
        print("\n[Step 5/5] Publishing Short to YouTube...")
        video_id = upload_short_to_youtube(
            video_path=final_video,
            title=script_data["title"],
            description=script_data["description"],
            tags=script_data.get("tags", []),
            privacy_status=privacy
        )
        upload_success = video_id is not None

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f" ✨ PIPELINE FINISHED IN {elapsed:.1f} SECONDS")
    if upload_success and video_id and video_id != "DRY_RUN_LOCAL":
        print(f" 📺 Published Short URL: https://youtube.com/shorts/{video_id}")
    elif not dry_run and not upload_success:
        print(f" ❌ UPLOAD FAILED — Video saved locally at: {final_video}")
    else:
        print(f" 📁 Local output: {final_video}")
    print("=" * 65)

    if not dry_run and not upload_success:
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Minecraft Facts YouTube Shorts Automation")
    parser.add_argument("--dry-run", action="store_true", help="Generate video without uploading to YouTube")
    parser.add_argument("--topic", type=str, default=None, help="Force a specific topic/fact")
    parser.add_argument("--username", type=str, default=None, help="Override Minecraft player skin username")
    parser.add_argument("--privacy", type=str, choices=["public", "unlisted", "private"], default=None, help="YouTube privacy status")
    
    args = parser.parse_args()
    run_pipeline(
        dry_run=args.dry_run,
        force_topic=args.topic,
        custom_username=args.username,
        privacy=args.privacy
    )

if __name__ == "__main__":
    main()
