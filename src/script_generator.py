"""AI Script Generator for Minecraft Facts YouTube Shorts.
Uses Google Gemini API and maintains history to ensure 100% unique scripts.
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, Any, List
from src.config_loader import load_config, get_gemini_api_key, DATA_DIR

USED_TOPICS_FILE = DATA_DIR / "used_topics.json"

DEFAULT_SYSTEM_PROMPT = """
You are a viral YouTube Shorts creator and Minecraft expert specializing in mind-blowing, obscure, and fascinating Minecraft facts and trivia.

Your goal is to produce a high-retention 35-50 second script for a YouTube Short.

RULES FOR VIRAL SHORTS SCRIPT:
1. THE HOOK (First 3 seconds): Must start with an immediate, gripping statement or question that triggers curiosity. (e.g., "Mojang accidentally added this feature in 2011...", "Do NOT craft this item if you value your world...", "Only 0.1% of Minecraft players know about this secret mob interaction...").
2. THE BODY (30 seconds): Fast-paced, concise explanation of the fact. Use conversational, excited, and punchy language. Avoid unnecessary filler words.
3. THE TWIST / CLIMAX: An extra interesting detail or practical application of the fact.
4. CALL TO ACTION (Final 3 seconds): Quick, natural CTA (e.g., "Subscribe if you learned something new!", "Did you already know this? Drop a comment!").
5. SCRIPT LENGTH: Exactly 75 to 110 words total (approx 35 to 45 seconds when spoken at 1.1x speed).
6. FORMAT: Output MUST be strictly valid JSON matching the requested schema. Do NOT include markdown ticks (```json).
"""

FALLBACK_FACTS = [
    {
        "topic": "Creeper Cat Phobia Mystery",
        "title": "Why Creepers Are TERRIFIED of Cats in Minecraft! #shorts",
        "description": "Ever wondered why the most dangerous mob in Minecraft runs away from tiny cats? Here is the secret lore and mechanic behind Creepers! #minecraft #minecraftfacts #shorts",
        "tags": ["minecraft", "creeper", "minecraft facts", "shorts", "gaming", "creeper cat"],
        "voiceover_script": "Ever wonder why Creepers are terrified of tiny cats? In early Minecraft development, Notch wanted a natural defense against the most destructive mob. Cats can see invisible mobs and hiss at Creepers, forcing their AI to flee up to 16 blocks away! Even charged creepers will instantly sprint away in terror. Keep a pet cat near your chests to protect your diamonds. Subscribe for more crazy Minecraft secrets!"
    },
    {
        "topic": "Ghast Crying Sound Lore",
        "title": "The DISTURBING Origin of Ghast Sounds in Minecraft! #shorts",
        "description": "You won't believe how C418 created the terrifying Ghast noises in Minecraft! #minecraft #minecraftlore #shorts",
        "tags": ["minecraft", "ghast", "minecraft lore", "c418", "shorts", "minecraft secrets"],
        "voiceover_script": "The terrifying sound of a Ghast crying in the Nether isn't a monster at all. It's actually a sleeping cat! When C418 was designing the audio for the Nether update, his cat accidentally woke up from a nap and made a bizarre screeching whine. He recorded it, pitched it down, and reversed parts of it to create the most haunting sound in Minecraft. Subscribe if this blew your mind!"
    },
    {
        "topic": "Nether Bed Explosion Mechanic",
        "title": "Why Beds EXPLODE in the Nether & The Secret Lore! #shorts",
        "description": "Why do beds explode when you sleep in the Nether? Here is the game mechanic explained! #minecraft #shorts #gaming",
        "tags": ["minecraft", "nether", "minecraft tips", "shorts", "gaming"],
        "voiceover_script": "Why do beds explode when you try to sleep in the Nether? In Minecraft lore, the Nether has no day and night cycle, meaning time simply does not exist. When you attempt to set your spawn point, the game tries to calculate the current time coordinate, resulting in a dimensional paradox that triggers a massive explosion with an explosion power of five! That is stronger than TNT! Subscribe for more insane facts!"
    },
    {
        "topic": "Shulker Color Easter Egg",
        "title": "You Can DYE Shulkers in Minecraft?! (Secret Feature) #shorts",
        "description": "Did you know you can change the color of living Shulkers in Minecraft? Here is how! #minecraft #minecraftshorts",
        "tags": ["minecraft", "shulker", "minecraft easter eggs", "shorts", "gaming"],
        "voiceover_script": "Did you know you can actually dye living Shulkers in Minecraft Bedrock edition? While Java players can only dye Shulker Boxes, Bedrock lets you use any dye on a wild Shulker to permanently change its shell color! Imagine building an entire rainbow defense army around your base. Subscribe for more secret features you didn't know!"
    },
    {
        "topic": "Skeleton Stray Transformation",
        "title": "The Secret Way Skeletons Become Strays! #shorts",
        "description": "How regular skeletons turn into Strays in powdered snow! #minecraft #minecraftsecrets #shorts",
        "tags": ["minecraft", "skeleton", "minecraft update", "shorts", "gaming"],
        "voiceover_script": "If you leave a regular Skeleton trapped inside powdered snow for just 7 seconds, something crazy happens. It begins to shake violently and transforms into a Stray, gaining slowness tipped arrows and an icy cloak! This means you can build an infinite tipped arrow farm using just a skeleton spawner and snow buckets. Subscribe for more top-tier Minecraft tricks!"
    }
]

def load_used_topics() -> List[str]:
    """Load previously used topics from disk to prevent duplicates."""
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

def save_used_topic(topic_title: str):
    """Save newly generated topic to history file."""
    topics = load_used_topics()
    if topic_title not in topics:
        topics.append(topic_title)
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2)

def generate_script_with_gemini(api_key: str, model_name: str, used_topics: List[str], topic_type: str = "hidden_mechanics") -> Dict[str, Any]:
    """Generate a unique viral Minecraft script using Google Gemini API."""
    import google.generativeai as genai
    genai.configure(api_key=api_key.strip())

    used_topics_summary = "\n".join(f"- {t}" for t in used_topics[-30:]) if used_topics else "None yet."

    user_prompt = f"""
Generate a brand new, highly engaging, 100% unique Minecraft Fact script for YouTube Shorts.

CATEGORY FOCUS: {topic_type.replace('_', ' ').title()}

CRITICAL CONSTRAINT: Do NOT repeat or closely mirror any of these previously covered topics:
{used_topics_summary}

Respond ONLY with a JSON object in this exact schema (no markdown code blocks, raw JSON only):
{{
  "topic": "Short 3-5 word topic name",
  "title": "Clicky & Viral YouTube Short Title with #shorts",
  "description": "Short SEO description with 3-5 hashtags including #shorts #minecraft",
  "tags": ["minecraft", "minecraft facts", "shorts", "gaming", "tag5", "tag6"],
  "voiceover_script": "The spoken voiceover script text (75 to 110 words total)."
}}
"""

    # Try requested model first, then fallback model aliases
    model_candidates = [model_name, "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    last_err = None

    for m_name in model_candidates:
        try:
            model = genai.GenerativeModel(
                model_name=m_name,
                system_instruction=DEFAULT_SYSTEM_PROMPT
            )
            response = model.generate_content(
                user_prompt,
                generation_config={
                    "temperature": 0.85,
                    "top_p": 0.95,
                    "response_mime_type": "application/json"
                }
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text.strip())
            return data
        except Exception as e:
            last_err = e
            continue

    raise last_err or RuntimeError("Failed to generate script with Gemini API")

def get_unique_script(force_topic: str = None) -> Dict[str, Any]:
    """Main interface to generate a fresh, unique script."""
    config = load_config()
    api_key = get_gemini_api_key()
    used_topics = load_used_topics()

    topic_types = config.get("script", {}).get("topic_types", ["hidden_mechanics", "mob_secrets", "creepy_lore"])
    selected_category = random.choice(topic_types)

    script_data = None

    if api_key:
        try:
            model_name = config.get("script", {}).get("model", "gemini-2.5-flash")
            print(f"[AI Script] Requesting new script using {model_name} (Category: {selected_category})...")
            script_data = generate_script_with_gemini(api_key, model_name, used_topics, selected_category)
            print(f"[AI Script] Successfully generated topic: '{script_data.get('topic')}'")
        except Exception as e:
            print(f"[AI Script Warning] Gemini API failed ({e}). Using curated fallback library...")
            script_data = None

    if not script_data:
        # Fallback mechanism: pick an unused fallback or random
        available_fallbacks = [f for f in FALLBACK_FACTS if f["topic"] not in used_topics]
        if not available_fallbacks:
            available_fallbacks = FALLBACK_FACTS
        script_data = random.choice(available_fallbacks)
        print(f"[AI Script] Selected curated fallback fact: '{script_data.get('topic')}'")

    if force_topic:
        script_data["topic"] = force_topic

    # Save to used topics
    save_used_topic(script_data["topic"])
    return script_data

if __name__ == "__main__":
    result = get_unique_script()
    print("\n--- GENERATED SCRIPT ---")
    print(json.dumps(result, indent=2))
