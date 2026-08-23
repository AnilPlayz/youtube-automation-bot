"""Asset preparation helper to download sample royalty-free gameplay & audio."""

import os
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GAMEPLAY_DIR = BASE_DIR / "assets" / "gameplay"
MUSIC_DIR = BASE_DIR / "assets" / "music"
FONTS_DIR = BASE_DIR / "assets" / "fonts"

def setup_assets():
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Checking asset directories...")
    print(f"  • Gameplay directory: {GAMEPLAY_DIR}")
    print(f"  • Music directory:    {MUSIC_DIR}")
    print(f"  • Fonts directory:    {FONTS_DIR}")

    # Note instructions for custom footage
    readme_gameplay = GAMEPLAY_DIR / "README.txt"
    if not readme_gameplay.exists():
        with open(readme_gameplay, "w", encoding="utf-8") as f:
            f.write(
                "Drop your 1080x1920 or 1920x1080 Minecraft parkour / gameplay MP4 files here!\n"
                "The pipeline will automatically pick random clips and crop them to 9:16 vertical Shorts format.\n"
                "If empty, a dynamic animated Minecraft-themed backdrop will be used automatically."
            )

    readme_music = MUSIC_DIR / "README.txt"
    if not readme_music.exists():
        with open(readme_music, "w", encoding="utf-8") as f:
            f.write(
                "Drop your background music MP3 files here (e.g. C418 style, royalty-free lofi chill beats)!\n"
                "The pipeline will automatically mix and duck the music under speech."
            )

    print("\nAssets initialized successfully!")

if __name__ == "__main__":
    setup_assets()
