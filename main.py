"""Master Pipeline Orchestrator for Minecraft Facts YouTube Shorts Automation."""

import argparse
import os
import sys
import time
from pathlib import Path

from src.config_loader import load_config, BASE_DIR
from src.script_generator import get_unique_script
from src.tts_engine import generate_voiceover
from src.video_composer import create_full_short_video
from src.youtube_uploader import upload_short_to_youtube

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

    # 1. Generate Unique Script
    print("\n[Step 1/4] Generating unique viral Minecraft fact script...")
    script_data = get_unique_script(force_topic=force_topic)
    print(f"  • Topic:       {script_data['topic']}")
    print(f"  • Title:       {script_data['title']}")
    print(f"  • Script Words: {len(script_data['voiceover_script'].split())} words")

    # 2. Generate Voiceover & Subtitles
    print("\n[Step 2/4] Synthesizing neural voiceover and extracting word timestamps...")
    audio_path = str(OUTPUT_DIR / f"voiceover_{timestamp}.mp3")
    audio_file, sub_chunks = generate_voiceover(
        script_text=script_data["voiceover_script"],
        output_audio_path=audio_path
    )
    print(f"  • Voiceover saved: {audio_file}")
    print(f"  • Subtitle chunks: {len(sub_chunks)} phrases synced")

    # 3. Assemble Video
    print("\n[Step 3/4] Compositing 9:16 Short (gameplay + subtitles + watermark + player avatar)...")
    video_output_path = str(OUTPUT_DIR / f"minecraft_short_{timestamp}.mp4")
    final_video = create_full_short_video(
        voiceover_path=audio_file,
        subtitle_chunks=sub_chunks,
        output_mp4_path=video_output_path,
        custom_username=custom_username
    )
    print(f"  • Rendered Video: {final_video}")

    # 4. Upload to YouTube
    if dry_run:
        print("\n[Step 4/4] ⚠️ DRY-RUN MODE: Skipping YouTube upload.")
        print(f"  • Video file ready at: {final_video}")
        video_id = "DRY_RUN_LOCAL"
    else:
        print("\n[Step 4/4] Publishing Short to YouTube...")
        video_id = upload_short_to_youtube(
            video_path=final_video,
            title=script_data["title"],
            description=script_data["description"],
            tags=script_data.get("tags", []),
            privacy_status=privacy
        )

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f" ✨ PIPELINE FINISHED IN {elapsed:.1f} SECONDS")
    if video_id and video_id != "DRY_RUN_LOCAL":
        print(f" 📺 Published Short URL: https://youtube.com/shorts/{video_id}")
    else:
        print(f" 📁 Local output: {final_video}")
    print("=" * 65)

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
