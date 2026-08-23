"""Configuration manager for the Minecraft YouTube Shorts automation system."""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

def load_config() -> dict:
    """Load config.yaml with environment variable overrides."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Environment variable overrides
    if os.getenv("MINECRAFT_USERNAME"):
        config.setdefault("player", {})["minecraft_username"] = os.getenv("MINECRAFT_USERNAME")
    
    if os.getenv("WATERMARK_TEXT"):
        config.setdefault("channel", {})["watermark_text"] = os.getenv("WATERMARK_TEXT")

    return config

def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        # Check standard GEMINI_API_KEY or GOOGLE_API_KEY
        key = os.getenv("GOOGLE_API_KEY")
    return key or ""
