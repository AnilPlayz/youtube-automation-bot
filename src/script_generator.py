"""AI Script Generator for Hindi Minecraft Facts YouTube Shorts.
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
You are a viral Hindi YouTube Shorts creator and Minecraft expert specializing in mind-blowing, obscure, and fascinating Minecraft facts and trivia.

Your goal is to produce a high-retention 35-50 second script for a YouTube Short entirely in HINDI (Devanagari script).

RULES FOR VIRAL SHORTS SCRIPT:
1. THE HOOK (First 3 seconds): Must start with an immediate, gripping statement or question in Hindi that triggers curiosity. (e.g., "क्या आपको पता है Minecraft में ये secret feature छुपा है...", "इस mob को कभी मत मारो वरना...", "सिर्फ 1% players को ये trick पता है...")
2. THE BODY (30 seconds): Fast-paced, concise explanation in Hindi. Use exciting, conversational Hinglish-style language mixing Hindi sentences with Minecraft terms in English.
3. THE TWIST / CLIMAX: An extra interesting detail or practical application.
4. CALL TO ACTION (Final 3 seconds): Quick Hindi CTA (e.g., "Subscribe karo agar ye nahi pata tha!", "Comment karo agar ye pehle se pata tha!").
5. SCRIPT LENGTH: Exactly 75 to 110 words total (approx 35 to 45 seconds when spoken).
6. FORMAT: Output MUST be strictly valid JSON matching the requested schema. Do NOT include markdown ticks.
7. IMPORTANT: The voiceover_script MUST be in Hindi (Devanagari script). Title and description can mix Hindi and English for SEO.
8. Include a "topic_theme" field: one of "nether", "end", "overworld", "ocean", "cave", "mob", "redstone", "magic".
"""

FALLBACK_FACTS = [
    {
        "topic": "Creeper बिल्ली से डर",
        "title": "Creeper बिल्लियों से क्यों डरते हैं? 😱🐱 #shorts #minecraft",
        "description": "Minecraft में Creeper बिल्लियों से क्यों भागते हैं? जानो असली राज! #minecraft #minecraftfacts #shorts #hindi",
        "tags": ["minecraft", "minecraft hindi", "minecraft facts", "shorts", "gaming", "creeper"],
        "topic_theme": "overworld",
        "voiceover_script": "क्या आपको पता है कि Minecraft का सबसे खतरनाक mob, Creeper, एक छोटी सी बिल्ली से डरता है? जब Notch ने game बनाया तो उन्होंने सोचा कि players को कोई natural defense चाहिए। बिल्लियाँ Creepers को 16 blocks दूर तक भगा सकती हैं! यहाँ तक कि Charged Creeper भी बिल्ली को देखकर भाग जाता है! अपने diamonds बचाने के लिए chest के पास बिल्ली रखो। Subscribe करो और ऐसे facts के लिए bell दबाओ!"
    },
    {
        "topic": "Ghast की रोने की आवाज़",
        "title": "Ghast की डरावनी आवाज़ का SHOCKING सच! 😨👻 #shorts #minecraft",
        "description": "Ghast की crying sound कैसे बनी? ये जानकर हैरान रह जाओगे! #minecraft #minecraftlore #shorts #hindi",
        "tags": ["minecraft", "ghast", "minecraft lore", "shorts", "gaming", "hindi"],
        "topic_theme": "nether",
        "voiceover_script": "Nether में Ghast की वो डरावनी रोने की आवाज़ सुनी है? वो असल में एक बिल्ली की आवाज़ है! जब C418 Nether का audio design कर रहे थे, उनकी बिल्ली अचानक नींद से उठी और एक अजीब सी चीख मारी। उन्होंने उसे record किया, pitch down किया, और reverse किया। बस यही Minecraft की सबसे haunting sound बन गई! अगर ये fact उड़ा दिया तो subscribe ज़रूर करो!"
    },
    {
        "topic": "Nether में Bed विस्फोट",
        "title": "Nether में Bed क्यों EXPLODE होता है? 💥🔥 #shorts #minecraft",
        "description": "Nether में bed से सोने की कोशिश मत करो! जानो क्यों फटता है bed! #minecraft #shorts #gaming #hindi",
        "tags": ["minecraft", "nether", "minecraft tips", "shorts", "gaming", "hindi"],
        "topic_theme": "nether",
        "voiceover_script": "Nether में bed पर सोने की कोशिश कभी मत करना! Minecraft lore के हिसाब से Nether में दिन और रात का cycle exist नहीं करता, मतलब time ही नहीं है वहाँ! जब तुम spawn point set करने की कोशिश करते हो, game time calculate करने लगता है और एक dimensional paradox trigger हो जाता है। धमाके की power 5 है, जो TNT से भी ज़्यादा है! Subscribe करो और ऐसे insane facts पाओ!"
    },
    {
        "topic": "Warden सबसे ताकतवर Mob",
        "title": "Warden को DEFEAT करना लगभग IMPOSSIBLE है! 😰⚔️ #shorts #minecraft",
        "description": "Minecraft का सबसे powerful mob Warden के बारे में shocking facts! #minecraft #shorts #warden #hindi",
        "tags": ["minecraft", "warden", "minecraft mob", "shorts", "gaming", "hindi"],
        "topic_theme": "cave",
        "voiceover_script": "Minecraft का सबसे ताकतवर mob Warden है और इसे मारना almost impossible है! इसकी health 500 है, जो Ender Dragon से भी ज़्यादा है! ये अंधा है लेकिन vibrations से तुम्हें track करता है। इसका sonic boom attack shields को भी bypass कर देता है! और सबसे डरावनी बात? अगर तुम invisible हो तो भी ये तुम्हें smell करके ढूंढ लेगा! Comment करो अगर तुमने Warden को कभी हराया है!"
    },
    {
        "topic": "End City का Elytra राज़",
        "title": "Elytra कैसे मिलता है? End City का HIDDEN Secret! 🪽✨ #shorts #minecraft",
        "description": "End City में Elytra ढूंढने का secret तरीका! #minecraft #shorts #elytra #hindi",
        "tags": ["minecraft", "elytra", "end city", "shorts", "gaming", "hindi"],
        "topic_theme": "end",
        "voiceover_script": "Elytra Minecraft का सबसे rare और powerful item है! ये सिर्फ End City के ships में मिलता है। लेकिन क्या पता है कि हर End City में ship नहीं होता? सिर्फ 56 percent cities में ship generate होता है! और Elytra को repair करने के लिए Phantom Membrane चाहिए, जो सिर्फ तभी मिलती है जब तुम 3 दिन तक ना सोओ! Subscribe करो gaming tips के लिए!"
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
            json.dump(topics, f, indent=2, ensure_ascii=False)

def generate_script_with_gemini(api_key: str, model_name: str, used_topics: List[str], topic_type: str = "hidden_mechanics") -> Dict[str, Any]:
    """Generate a unique viral Hindi Minecraft script using Google Gemini API."""
    import google.generativeai as genai
    genai.configure(api_key=api_key.strip())

    used_topics_summary = "\n".join(f"- {t}" for t in used_topics[-30:]) if used_topics else "None yet."

    user_prompt = f"""
Generate a brand new, highly engaging, 100% unique Minecraft Fact script for YouTube Shorts IN HINDI (Devanagari script).

CATEGORY FOCUS: {topic_type.replace('_', ' ').title()}

CRITICAL CONSTRAINT: Do NOT repeat or closely mirror any of these previously covered topics:
{used_topics_summary}

Respond ONLY with a JSON object in this exact schema (no markdown code blocks, raw JSON only):
{{
  "topic": "Short 3-5 word topic name (Hindi or mix)",
  "title": "Viral YouTube Short Title mixing Hindi + English with #shorts",
  "description": "Short SEO description with 3-5 hashtags including #shorts #minecraft #hindi",
  "tags": ["minecraft", "minecraft hindi", "minecraft facts", "shorts", "gaming", "tag6"],
  "topic_theme": "one of: nether, end, overworld, ocean, cave, mob, redstone, magic",
  "voiceover_script": "The spoken voiceover script text IN HINDI (Devanagari) (75 to 110 words total)."
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
            # Ensure topic_theme exists
            if "topic_theme" not in data:
                data["topic_theme"] = random.choice(["nether", "end", "overworld", "ocean", "cave", "mob", "redstone", "magic"])
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

    # Ensure topic_theme exists
    if "topic_theme" not in script_data:
        script_data["topic_theme"] = random.choice(["nether", "end", "overworld", "ocean", "cave", "mob", "redstone", "magic"])

    # Save to used topics
    save_used_topic(script_data["topic"])
    return script_data

if __name__ == "__main__":
    result = get_unique_script()
    print("\n--- GENERATED SCRIPT ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
