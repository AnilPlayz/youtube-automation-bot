"""Script Generator for Hindi Minecraft Facts YouTube Shorts.
500-script library (100 topics × 5 Hindi variations).
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, Any, List
from src.config_loader import load_config, get_gemini_api_key, DATA_DIR

USED_TOPICS_FILE = DATA_DIR / "used_topics.json"
SCRIPTS_LIBRARY_FILE = DATA_DIR / "scripts_500.json"

# 5 Hindi Hook/CTA variation templates
VARIATIONS = [
    {
        "hook": "रुको—क्या तुम्हें ये Minecraft fact पता था?",
        "extension": "",
        "cta": "और facts के लिए follow करो!"
    },
    {
        "hook": "ये fact ज़्यादातर Minecraft players miss कर देते हैं!",
        "extension": " और सबसे crazy बात ये है कि इससे तुम्हारा gameplay पूरा बदल सकता है।",
        "cta": "बाद के लिए save करो!"
    },
    {
        "hook": "ये Minecraft fact सुनकर fake लगेगा, लेकिन ये 100% real है!",
        "extension": " ज़्यादातर casual players इस mechanic के बारे में सोचते भी नहीं।",
        "cta": "क्या तुम्हें ये पहले से पता था?"
    },
    {
        "hook": "शायद तुमने Minecraft में ये कभी notice नहीं किया होगा।",
        "extension": " ये छोटी सी detail survival में बहुत काम आ सकती है।",
        "cta": "ये किसी Minecraft player को भेजो!"
    },
    {
        "hook": "Scroll करने से पहले ये quick Minecraft fact सुन लो!",
        "extension": " अब तुम्हारे पास दोस्तों पर flex करने के लिए एक नया fact है।",
        "cta": "Minecraft का वो हिस्सा जो तुमने शायद कभी notice नहीं किया!"
    }
]

# Hindi translations for core facts
HINDI_FACTS = {
    "Creeper origin": "Creepers actually एक failed pig model से बने थे!",
    "Creeper warning": "Creeper explode होने से पहले flash करता है!",
    "Charged Creeper": "Lightning एक normal Creeper को charged Creeper में बदल सकती है!",
    "Enderman water": "Endermen को पानी और बारिश से damage होता है!",
    "Enderman blocks": "Endermen कुछ specific blocks उठा सकते हैं!",
    "End portal": "Activated End portal तुम्हें सीधा End dimension में भेज देता है!",
    "Dragon egg": "Dragon egg पहली बार Ender Dragon को हराने के बाद appear होता है!",
    "Nether": "Nether एक dangerous lava से भरा dimension है!",
    "Netherite": "Netherite gear diamond gear से ज़्यादा durable होता है!",
    "Ancient debris": "Ancient debris से netherite बनता है!",
    "Ghast": "Ghasts explosive fireballs shoot करते हैं!",
    "Blaze": "Blazes blaze rods drop करते हैं जो progression के लिए ज़रूरी हैं!",
    "Wither": "Wither एक player-summoned boss है!",
    "Ocean Monument": "Ocean Monuments guardians से protected होते हैं!",
    "Sponge": "Sponges आस-पास का पानी absorb कर सकते हैं!",
    "Axolotl": "Axolotls underwater enemies से लड़ने में मदद कर सकते हैं!",
    "Dolphin": "Dolphins nearby swimmers को speed boost देते हैं!",
    "Turtle": "Baby turtles बड़े होने पर scutes drop करते हैं!",
    "Villager jobs": "Villagers job-site blocks से professions ले सकते हैं!",
    "Emerald": "Emeralds villager trading की main currency हैं!",
    "Iron golem": "Iron golems villages को protect करते हैं और players बना भी सकते हैं!",
    "Cats": "Cats creepers को भगा सकती हैं!",
    "Phantom": "कई in-game दिन ना सोने पर Phantoms appear हो सकते हैं!",
    "Bed explosion": "Nether या End में beds explode हो जाते हैं!",
    "Respawn anchor": "Respawn anchors Nether में respawn point set कर सकते हैं!",
    "Lodestone": "Lodestone compass को किसी भी chosen location की तरफ point करा सकता है!",
    "Recovery compass": "Recovery compass तुम्हारी last death location की तरफ point करता है!",
    "Beacon": "Beacons powerful status effects provide कर सकते हैं!",
    "Enchanting": "Enchanting में experience और lapis lazuli लगती है!",
    "Anvil": "Anvils items को repair, rename और combine कर सकते हैं!",
    "Grindstone": "Grindstones ज़्यादातर enchantments remove कर सकते हैं!",
    "Smithing table": "Smithing tables equipment upgrade और armor trims handle करते हैं!",
    "Redstone": "Redstone machines और logic systems को power करता है!",
    "Piston": "Pistons powered होने पर blocks push कर सकते हैं!",
    "Sticky piston": "Sticky pistons blocks को वापस pull कर सकते हैं!",
    "Observer": "Observers block updates detect करके redstone pulses output करते हैं!",
    "Hopper": "Hoppers inventories के बीच items move करते हैं!",
    "Dispenser": "Dispensers certain items को activate या launch कर सकते हैं!",
    "Note block": "Note blocks अलग-अलग musical notes बना सकते हैं!",
    "Mending": "Mending collected experience से equipment repair करता है!",
    "Fortune": "Fortune certain block drops बढ़ा सकता है!",
    "Silk Touch": "Silk Touch blocks को उनके original form में collect करने देता है!",
    "Unbreaking": "Unbreaking items को durability loss avoid करने का chance देता है!",
    "Efficiency": "Efficiency बहुत सारे tools को blocks तोड़ने में faster बनाता है!",
    "Feather Falling": "Feather Falling fall damage कम करता है!",
    "Respiration": "Respiration underwater breathing time बढ़ाता है!",
    "Depth Strider": "Depth Strider underwater movement faster बनाता है!",
    "Warden": "Warden को लड़ने के बजाय avoid करने के लिए design किया गया है!",
    "Ancient City": "Ancient Cities deep dark में बहुत गहराई में generate होती हैं!",
    "Allay": "Allays matching dropped items collect कर सकते हैं!",
    "Copper": "Copper oxidize होने पर अपनी appearance बदलता है!",
    "Lightning rod": "Lightning rods lightning strikes attract करते हैं!",
    "Amethyst": "Amethyst geodes में budding amethyst और clusters होते हैं!",
    "Spyglass": "Spyglasses players को view zoom करने देते हैं!",
    "Powder snow": "Powder snow में entities डूब सकती हैं!",
    "Goat": "Goats nearby entities को ram कर सकते हैं!",
    "Bee": "Bees pollen collect करके अपने nests या hives में लौटती हैं!",
    "Honey": "Honey bottles poison remove कर सकती हैं!",
    "Honey block": "Honey blocks की special sticky movement properties होती हैं!",
    "Slime": "बड़े slimes मरने पर छोटे slimes में split हो सकते हैं!",
    "Witch": "Witches combat में potions use करती हैं!",
    "Vex": "Vexes evokers द्वारा summon किए जाने वाले flying mobs हैं!",
    "Raid": "Raids सही conditions में villages पर attack करती हैं!",
    "Totem": "Totem of Undying सही तरीके से hold करने पर lethal damage से बचा सकता है!",
    "Woodland mansion": "Woodland Mansions rare illager structures हैं!",
    "Stronghold": "Strongholds में End portals होते हैं!",
    "Eye of Ender": "Eyes of ender strongholds locate करने में मदद करते हैं!",
    "Ender pearl": "Ender pearls throw करने पर players को teleport करते हैं!",
    "Golden apple": "Golden apples powerful temporary effects provide करते हैं!",
    "Water bucket": "Water bucket fall damage से बचा सकता है!",
    "Lava bucket": "Lava bucket weapon भी है और strong furnace fuel भी!",
    "Soul sand bubbles": "Soul sand underwater upward bubble columns बनाता है!",
    "Magma bubbles": "Magma blocks underwater downward bubble columns बनाते हैं!",
    "Boat": "Boats players और बहुत सारे mobs को transport कर सकती हैं!",
    "Minecart": "Minecarts rails के along travel करती हैं!",
    "Elytra": "Elytra players को हवा में glide करने देता है!",
    "Firework rockets": "Firework rockets elytra flight boost कर सकते हैं!",
    "Shulker box": "Shulker boxes तोड़ने पर भी अपना content रखते हैं!",
    "Ender chest": "Ender chests personal shared storage provide करते हैं!",
    "Furnace": "Furnaces fuel से smelt और cook करते हैं!",
    "Blast furnace": "Blast furnaces certain materials faster process करते हैं!",
    "Smoker": "Smokers regular furnaces से faster food cook करते हैं!",
    "Campfire": "Campfires बिना furnace fuel के food cook कर सकते हैं!",
    "Torch": "Torches light देते हैं और hostile mob spawning रोकने में मदद करते हैं!",
    "Glass": "Glass sand को smelt करके बनता है!",
    "Concrete": "Concrete powder पानी से touch होने पर concrete बन जाता है!",
    "Sheep": "Sheep को shear करके wool मिलता है!",
    "Milk": "Milk बहुत सारे status effects remove करता है!",
    "Strider": "Striders lava पर चल सकते हैं!",
    "Piglin": "Piglins gold armor ना पहनने वाले players पर hostile हो जाते हैं!",
    "Piglin bartering": "Piglins gold ingots देने पर barter कर सकते हैं!",
    "Bastion": "Bastion Remnants dangerous Nether structures हैं!",
    "Nether fortress": "Nether fortresses में blazes और wither skeletons होते हैं!",
    "Mushroom fields": "Mushroom fields rare हैं और unusual mob-spawning behavior रखते हैं!",
    "Mooshroom": "Mooshrooms mushroom stew provide कर सकते हैं!",
    "Panda": "Pandas की अलग-अलग personalities और behaviors होते हैं!",
    "Bamboo": "Bamboo तेज़ी से grow होता है और building में use हो सकता है!",
    "Scaffolding": "Scaffolding players को safely ऊपर build करने में मदद करता है!",
    "TNT": "TNT primed होने पर explode हो जाता है!",
    "Gunpowder": "Gunpowder TNT और fireworks बनाने में use होता है!"
}


def load_scripts_library() -> List[Dict[str, Any]]:
    """Load the 100-topic scripts library."""
    if not SCRIPTS_LIBRARY_FILE.exists():
        return []
    try:
        with open(SCRIPTS_LIBRARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Script Generator] ERROR: Failed to load scripts library: {e}")
        return []


def expand_topic_to_script(topic_entry: Dict[str, Any], variation_idx: int = None) -> Dict[str, Any]:
    """Expand a topic into a full Hindi script."""
    if variation_idx is None:
        variation_idx = random.randint(0, 4)

    var = VARIATIONS[variation_idx]
    topic = topic_entry["topic"]
    theme = topic_entry.get("theme", "overworld")

    # Get Hindi fact translation
    hindi_fact = HINDI_FACTS.get(topic, topic_entry["fact"])

    # Build full Hindi voiceover
    voiceover = f"{var['hook']} {hindi_fact}{var['extension']} {var['cta']}"

    # Build YouTube title (Hindi + English mix for SEO)
    title = f"{topic} — {var['hook'][:30]}... #shorts #minecraft"
    if len(title) > 90:
        title = f"{topic} — Minecraft Fact! #shorts"

    description = (
        f"{var['hook']} {hindi_fact} "
        f"#minecraft #minecraftfacts #shorts #gaming #hindi #minecrafthindi"
    )

    tags = [
        "minecraft", "minecraft hindi", "minecraft facts", "shorts", "gaming",
        "minecraft secrets", "hindi gaming", topic.lower().replace(" ", "")
    ]

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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USED_TOPICS_FILE.exists():
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Script Generator] ERROR: Failed to load used topics: {e}")
        return []


def save_used_topic(script_id: str):
    topics = load_used_topics()
    if script_id not in topics:
        topics.append(script_id)
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2, ensure_ascii=False)


def get_unique_script(force_topic: str = None) -> Dict[str, Any]:
    """Get a fresh, unique Hindi script from the 500-script library."""
    used_ids = load_used_topics()
    library = load_scripts_library()

    if not library:
        return {
            "topic": "Creeper origin",
            "script_id": "fallback_1",
            "title": "Creepers एक FAILED PIG MODEL से बने! #shorts #minecraft",
            "description": "क्या पता था Creepers एक coding accident थे? #minecraft #shorts",
            "tags": ["minecraft", "shorts", "gaming", "hindi"],
            "voiceover_script": "रुको—क्या तुम्हें ये Minecraft fact पता था? Creepers actually एक failed pig model से बने थे! और facts के लिए follow करो!",
            "topic_theme": "mob"
        }

    all_scripts = []
    for topic_entry in library:
        for v_idx in range(5):
            script_id = f"{topic_entry['topic']}_v{v_idx + 1}"
            all_scripts.append((topic_entry, v_idx, script_id))

    available = [(t, v, sid) for t, v, sid in all_scripts if sid not in used_ids]

    if not available:
        print("[Script Generator] All 500 scripts used! Resetting for fresh cycle.")
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        available = all_scripts

    if force_topic:
        topic_matches = [(t, v, sid) for t, v, sid in available if force_topic.lower() in t["topic"].lower()]
        if topic_matches:
            available = topic_matches

    topic_entry, var_idx, script_id = random.choice(available)
    script_data = expand_topic_to_script(topic_entry, var_idx)

    print(f"[Script Generator] Selected: '{script_data['script_id']}' ({len(available) - 1} remaining)")
    print(f"  • Topic:       {script_data['topic']}")
    print(f"  • Title:       {script_data['title']}")
    print(f"  • Theme:       {script_data['topic_theme']}")

    save_used_topic(script_data["script_id"])
    return script_data
