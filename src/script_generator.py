"""Script Generator for Minecraft Facts YouTube Shorts.
Uses a 500-script pre-built library (100 topics × 5 variations) with optional Gemini AI generation.
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, Any, List
from src.config_loader import load_config, get_gemini_api_key, DATA_DIR

USED_TOPICS_FILE = DATA_DIR / "used_topics.json"
SCRIPTS_LIBRARY_FILE = DATA_DIR / "scripts_500.json"

# 5 Hook/CTA variation templates
VARIATIONS = [
    {
        "hook": "WAIT—did you know this Minecraft fact?",
        "extension": "",
        "cta": "Follow for more Minecraft facts!"
    },
    {
        "hook": "Minecraft players usually miss this!",
        "extension": " And here is the crazy part: this can actually change how you play the game.",
        "cta": "Save this for later!"
    },
    {
        "hook": "This Minecraft fact sounds fake, but it is real!",
        "extension": " Most casual players never think about this mechanic.",
        "cta": "Did you know this already?"
    },
    {
        "hook": "You probably never noticed this in Minecraft.",
        "extension": " That tiny detail can be surprisingly useful in survival.",
        "cta": "Send this to a Minecraft player!"
    },
    {
        "hook": "Quick Minecraft fact before you scroll!",
        "extension": " Now you have a new Minecraft fact to flex on your friends.",
        "cta": "Part of Minecraft you probably never noticed!"
    }
]


def load_scripts_library() -> List[Dict[str, Any]]:
    """Load the 100-topic scripts library."""
    if not SCRIPTS_LIBRARY_FILE.exists():
        return []
    try:
        with open(SCRIPTS_LIBRARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def expand_topic_to_script(topic_entry: Dict[str, Any], variation_idx: int = None) -> Dict[str, Any]:
    """
    Expand a compact topic entry into a full script using one of the 5 variations.
    Returns a complete script dict ready for video generation.
    """
    if variation_idx is None:
        variation_idx = random.randint(0, 4)

    var = VARIATIONS[variation_idx]
    topic = topic_entry["topic"]
    fact = topic_entry["fact"]
    theme = topic_entry.get("theme", "overworld")

    # Build full voiceover: HOOK + FACT + EXTENSION + CTA
    voiceover = f"{var['hook']} {fact}{var['extension']} {var['cta']}"

    # Build YouTube title
    title = f"{topic} — {var['hook']} #shorts #minecraft"
    if len(title) > 90:
        title = f"{topic} — Minecraft Fact! #shorts"

    # Build description
    description = (
        f"{var['hook']} {fact} "
        f"#minecraft #minecraftfacts #shorts #gaming #minecraftsecrets"
    )

    # Build tags
    tags = [
        "minecraft", "minecraft facts", "shorts", "gaming",
        "minecraft secrets", "minecraft tips",
        topic.lower().replace(" ", "")
    ]

    # Unique script ID for tracking (topic + variation)
    script_id = f"{topic}_v{variation_idx + 1}"

    return {
        "topic": topic,
        "script_id": script_id,
        "title": title,
        "description": description,
        "tags": tags,
        "voiceover_script": voiceover,
        "topic_theme": theme
    }


def load_used_topics() -> List[str]:
    """Load previously used script IDs from disk to prevent duplicates."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USED_TOPICS_FILE.exists():
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_used_topic(script_id: str):
    """Save newly used script ID to history file."""
    topics = load_used_topics()
    if script_id not in topics:
        topics.append(script_id)
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2)


def get_unique_script(force_topic: str = None) -> Dict[str, Any]:
    """
    Main interface to get a fresh, unique script from the 500-script library.
    Cycles through all 100 topics × 5 variations = 500 unique scripts.
    After exhausting all 500, resets and starts over.
    """
    used_ids = load_used_topics()
    library = load_scripts_library()

    if not library:
        print("[Script Generator] WARNING: scripts_500.json not found. Using hardcoded fallback.")
        return {
            "topic": "Creeper origin",
            "script_id": "fallback_1",
            "title": "Creepers came from a FAILED PIG MODEL! #shorts #minecraft",
            "description": "Did you know Creepers were a coding accident? #minecraft #shorts",
            "tags": ["minecraft", "shorts", "gaming"],
            "voiceover_script": "WAIT—did you know this Minecraft fact? Creepers came from a failed pig model. Follow for more Minecraft facts!",
            "topic_theme": "mob"
        }

    # Build all 500 possible script IDs
    all_scripts = []
    for topic_entry in library:
        for v_idx in range(5):
            script_id = f"{topic_entry['topic']}_v{v_idx + 1}"
            all_scripts.append((topic_entry, v_idx, script_id))

    # Filter out used ones
    available = [(t, v, sid) for t, v, sid in all_scripts if sid not in used_ids]

    if not available:
        # All 500 used! Reset history and start fresh
        print("[Script Generator] All 500 scripts used! Resetting history for fresh cycle.")
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        available = all_scripts

    # If force_topic, filter by topic name
    if force_topic:
        topic_matches = [(t, v, sid) for t, v, sid in available if force_topic.lower() in t["topic"].lower()]
        if topic_matches:
            available = topic_matches

    # Pick a random available script
    topic_entry, var_idx, script_id = random.choice(available)
    script_data = expand_topic_to_script(topic_entry, var_idx)

    print(f"[Script Generator] Selected: '{script_data['script_id']}' ({len(available) - 1} remaining)")
    print(f"  • Topic:       {script_data['topic']}")
    print(f"  • Title:       {script_data['title']}")
    print(f"  • Theme:       {script_data['topic_theme']}")
    print(f"  • Script Words: {len(script_data['voiceover_script'].split())} words")

    # Save to used list
    save_used_topic(script_data["script_id"])
    return script_data


if __name__ == "__main__":
    result = get_unique_script()
    print("\n--- GENERATED SCRIPT ---")
    print(json.dumps(result, indent=2))
