"""Video Composition Engine for Hindi Minecraft Facts Shorts.
Layout: Character CENTER (in front), Professional captions BEHIND character,
        Evolving animated non-looping background.
"""

import math
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Fix Pillow 10+ compatibility with moviepy 1.0.3
# moviepy uses Image.ANTIALIAS which was removed in Pillow 10+
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        VideoClip,
        ColorClip
    )
except ImportError:
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        VideoClip,
        ColorClip
    )

from src.config_loader import load_config, ASSETS_DIR
from src.skin_renderer import get_player_avatar, generate_avatar_frame

GAMEPLAY_DIR = ASSETS_DIR / "gameplay"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"

# ── Theme color palettes ──
THEME_PALETTES = {
    "nether": {
        "bg_start": (60, 10, 5), "bg_end": (20, 5, 30),
        "accent": (255, 100, 30), "glow": (255, 60, 20),
        "particle": (255, 180, 50),
        "subtitle_fill": (255, 200, 60), "subtitle_glow": (255, 80, 30),
    },
    "end": {
        "bg_start": (15, 5, 40), "bg_end": (5, 15, 25),
        "accent": (200, 120, 255), "glow": (180, 80, 255),
        "particle": (220, 180, 255),
        "subtitle_fill": (220, 180, 255), "subtitle_glow": (140, 255, 200),
    },
    "overworld": {
        "bg_start": (10, 45, 15), "bg_end": (15, 20, 45),
        "accent": (100, 220, 80), "glow": (80, 200, 60),
        "particle": (180, 255, 100),
        "subtitle_fill": (255, 230, 0), "subtitle_glow": (0, 255, 128),
    },
    "ocean": {
        "bg_start": (5, 20, 60), "bg_end": (10, 10, 35),
        "accent": (50, 180, 255), "glow": (30, 150, 255),
        "particle": (100, 220, 255),
        "subtitle_fill": (100, 240, 255), "subtitle_glow": (255, 220, 80),
    },
    "cave": {
        "bg_start": (20, 18, 30), "bg_end": (10, 12, 18),
        "accent": (120, 200, 255), "glow": (80, 180, 240),
        "particle": (200, 220, 255),
        "subtitle_fill": (200, 230, 255), "subtitle_glow": (255, 200, 80),
    },
    "mob": {
        "bg_start": (35, 10, 12), "bg_end": (15, 15, 30),
        "accent": (255, 60, 80), "glow": (255, 40, 60),
        "particle": (255, 150, 100),
        "subtitle_fill": (255, 100, 120), "subtitle_glow": (255, 255, 80),
    },
    "redstone": {
        "bg_start": (40, 5, 5), "bg_end": (15, 10, 25),
        "accent": (255, 0, 0), "glow": (255, 50, 50),
        "particle": (255, 120, 80),
        "subtitle_fill": (255, 80, 80), "subtitle_glow": (255, 255, 100),
    },
    "magic": {
        "bg_start": (25, 10, 50), "bg_end": (10, 20, 35),
        "accent": (180, 100, 255), "glow": (150, 80, 255),
        "particle": (255, 150, 255),
        "subtitle_fill": (255, 180, 255), "subtitle_glow": (100, 255, 200),
    },
}

def ensure_assets_dirs():
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

def get_theme(topic_theme: str) -> dict:
    return THEME_PALETTES.get(topic_theme, THEME_PALETTES["overworld"])

def get_font(size: int = 70) -> ImageFont.ImageFont:
    """Load bold font with Hindi support."""
    for ext in ["*.ttf", "*.otf"]:
        for font_file in FONTS_DIR.glob(ext):
            try:
                return ImageFont.truetype(str(font_file), size)
            except Exception as e:
                print(f"[Video Composer] Font load failed for {font_file.name}: {e}")
                pass

    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\NirmalaB.ttf",
        "C:\\Windows\\Fonts\\mangal.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for c in candidates:
        try:
            f = ImageFont.truetype(c, size)
            f.getbbox("क")
            return f
        except Exception as e:
            print(f"[Video Composer] System font fallback failed for {c}: {e}")
            continue
    return ImageFont.load_default()


def get_ascii_font(size: int = 36) -> ImageFont.ImageFont:
    """Load a font that reliably renders ASCII characters (for watermark etc)."""
    # Prioritize fonts known to handle ASCII well
    ascii_candidates = [
        # System fonts (ASCII-safe)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    # Also check user's custom fonts
    for ext in ["*.ttf", "*.otf"]:
        for font_file in FONTS_DIR.glob(ext):
            try:
                f = ImageFont.truetype(str(font_file), size)
                f.getbbox("@Anil-Patel-29")
                return f
            except Exception as e:
                print(f"[Video Composer] ASCII font load failed for {font_file.name}: {e}")
                pass

    for c in ascii_candidates:
        try:
            f = ImageFont.truetype(c, size)
            # Verify it can render ASCII properly
            f.getbbox("@Anil-Patel-29")
            return f
        except Exception as e:
            print(f"[Video Composer] ASCII system font fallback failed for {c}: {e}")
            continue
    return ImageFont.load_default()


def create_evolving_backdrop(duration: float, theme: dict, width: int = 1080, height: int = 1920) -> VideoClip:
    """
    Creates a non-looping, continuously evolving animated background.
    - Gradient colors shift over time (not repeating)
    - Per-theme animated effects (particles, glows, shapes)
    - Radial pulse effects evolve
    """
    print("[Video Composer] Generating evolving animated backdrop...")

    bg_start = theme["bg_start"]
    bg_end = theme["bg_end"]
    accent = theme["accent"]
    glow_color = theme["glow"]
    particle_color = theme["particle"]

    # Detect theme name from colors for per-theme effects
    theme_name = "generic"
    for name, pal in THEME_PALETTES.items():
        if pal == theme:
            theme_name = name
            break

    # Pre-generate particle data (each has unique lifecycle)
    num_particles = 50 if theme_name in ("nether", "magic", "mob") else 35
    particles = []
    for i in range(num_particles):
        particles.append({
            "x": random.randint(0, width),
            "y": random.randint(0, height),
            "size": random.randint(3, 16 if theme_name in ("nether", "magic") else 12),
            "speed_y": random.uniform(15, 80 if theme_name == "nether" else 50),
            "drift_x": random.uniform(-25, 25),
            "phase": random.uniform(0, math.pi * 2),
            "brightness": random.uniform(0.3, 1.0),
            "birth_t": random.uniform(0, duration * 0.4),
        })

    # Theme-specific extra elements
    num_rings = 3 if theme_name in ("end", "magic") else 0
    num_eyes = 6 if theme_name == "mob" else 0
    num_bubbles = 15 if theme_name == "ocean" else 0
    num_crystals = 8 if theme_name == "cave" else 0
    num_leaves = 12 if theme_name == "overworld" else 0
    num_sparks = 10 if theme_name == "redstone" else 0

    eye_data = [{"x": random.randint(50, width - 50), "y": random.randint(100, height - 200),
                  "blink_phase": random.uniform(0, math.pi * 2)} for _ in range(num_eyes)]
    bubble_data = [{"x": random.randint(50, width - 50), "y": random.randint(height // 2, height),
                     "speed": random.uniform(20, 60), "size": random.randint(4, 12),
                     "phase": random.uniform(0, math.pi * 2)} for _ in range(num_bubbles)]
    crystal_data = [{"x": random.randint(0, width), "y": random.randint(0, height),
                      "size": random.randint(20, 60), "phase": random.uniform(0, math.pi * 2),
                      "brightness": random.uniform(0.3, 0.8)} for _ in range(num_crystals)]
    leaf_data = [{"x": random.randint(0, width), "y": random.randint(-100, height),
                   "speed_x": random.uniform(-15, 15), "speed_y": random.uniform(20, 50),
                   "rotation": random.uniform(0, 360), "rot_speed": random.uniform(-90, 90),
                   "size": random.randint(6, 14)} for _ in range(num_leaves)]
    spark_data = [{"x": random.randint(0, width), "y": random.randint(0, height),
                    "phase": random.uniform(0, math.pi * 2),
                    "brightness": random.uniform(0.4, 1.0)} for _ in range(num_sparks)]

    def make_frame(t):
        progress = t / max(duration, 0.01)
        phase1 = min(1.0, progress * 2)
        phase2 = max(0.0, (progress - 0.5) * 2)

        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Vectorized vertical gradient + time evolution
        y_ratios = np.linspace(0, 1, height).reshape(-1, 1)
        wave = np.sin(y_ratios * 8 + t * 1.5) * 8

        r_base = int(bg_start[0] * (1 - phase1) + bg_end[0] * phase1)
        g_base = int(bg_start[1] * (1 - phase1) + bg_end[1] * phase1)
        b_base = int(bg_start[2] * (1 - phase1) + bg_end[2] * phase1)

        r_col = (r_base + accent[0] * phase2 * 0.15 * (1 - y_ratios) + wave).astype(np.float32)
        g_col = (g_base + accent[1] * phase2 * 0.15 * y_ratios + wave * 0.5).astype(np.float32)
        b_col = (b_base + accent[2] * phase2 * 0.15 + wave * 0.7).astype(np.float32)

        frame[:, :, 0] = np.clip(r_col, 0, 255).astype(np.uint8)
        frame[:, :, 1] = np.clip(g_col, 0, 255).astype(np.uint8)
        frame[:, :, 2] = np.clip(b_col, 0, 255).astype(np.uint8)

        # ── Radial pulse from center ──
        cy, cx = height // 2, width // 2
        pulse_radius = int(200 + t * 80 + math.sin(t * 2) * 100)
        pulse_intensity = max(0, 0.2 - progress * 0.15)

        y_coords, x_coords = np.ogrid[:height, :width]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
        pulse_mask = np.clip(1.0 - np.abs(dist - pulse_radius) / 150, 0, 1) * pulse_intensity

        for c in range(3):
            frame[:, :, c] = np.clip(
                frame[:, :, c].astype(float) + pulse_mask * accent[c] * 0.5,
                0, 255
            ).astype(np.uint8)

        # ── Vignette ──
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        vig_strength = 0.5 + 0.15 * math.sin(t * 1.2)
        vignette = 1.0 - (dist / max_dist) * vig_strength
        vignette = np.clip(vignette, 0.25, 1.0)
        frame = (frame * vignette[:, :, np.newaxis]).astype(np.uint8)

        # ── Theme-specific effects (drawn on top) ──
        frame_pil = Image.fromarray(frame)
        pdraw = ImageDraw.Draw(frame_pil)

        # Floating particles (all themes)
        for p in particles:
            age = t - p["birth_t"]
            if age < 0:
                continue
            py = (p["y"] - age * p["speed_y"]) % height
            px = p["x"] + math.sin(age * 1.2 + p["phase"]) * 30 + p["drift_x"] * age * 0.3
            px = px % width
            life_alpha = min(1.0, age * 2) * max(0.0, 1.0 - (age / (duration * 0.8)))
            bright = p["brightness"] * life_alpha
            if bright < 0.05:
                continue
            sz = p["size"]
            pc = tuple(int(c * bright) for c in particle_color)
            gc = tuple(int(c * bright * 0.3) for c in glow_color)
            pdraw.ellipse([px - sz - 5, py - sz - 5, px + sz + 5, py + sz + 5], fill=gc)
            pdraw.ellipse([px - sz, py - sz, px + sz, py + sz], fill=pc)

        # ── Nether: Lava pool glow at bottom ──
        if theme_name == "nether":
            lava_y = int(height * 0.85)
            lava_intensity = int(80 + 40 * math.sin(t * 2.5))
            for row in range(lava_y, min(lava_y + 120, height)):
                alpha = max(0, int(lava_intensity * (1.0 - (row - lava_y) / 120)))
                for col in range(width):
                    wave_off = int(math.sin(col * 0.02 + t * 3) * 15)
                    if abs(row - (lava_y + wave_off)) < 40:
                        r, g, b = frame_pil.getpixel((col, row))[:3]
                        frame_pil.putpixel((col, row), (
                            min(255, r + alpha),
                            min(255, g + alpha // 4),
                            min(255, b)
                        ))

        # ── End: Purple portal rings ──
        if theme_name == "end":
            for ring_i in range(num_rings):
                ring_r = int(100 + ring_i * 80 + math.sin(t * 1.5 + ring_i) * 40)
                ring_alpha = int(60 - ring_i * 15)
                if ring_alpha > 0:
                    for angle_deg in range(0, 360, 3):
                        angle = math.radians(angle_deg + t * 20)
                        rx = int(cx + ring_r * math.cos(angle))
                        ry = int(cy + ring_r * math.sin(angle) * 0.6)
                        if 0 <= rx < width and 0 <= ry < height:
                            r, g, b = frame_pil.getpixel((rx, ry))[:3]
                            frame_pil.putpixel((rx, ry), (
                                min(255, r + ring_alpha // 2),
                                min(255, g),
                                min(255, b + ring_alpha)
                            ))

        # ── Ocean: Rising bubbles ──
        if theme_name == "ocean":
            for bub in bubble_data:
                age = t * bub["speed"]
                by = int((bub["y"] - age) % height)
                bx = int(bub["x"] + math.sin(t + bub["phase"]) * 20)
                bs = bub["size"]
                if 0 <= bx < width and 0 <= by < height:
                    bubble_alpha = int(120 + 40 * math.sin(t * 2 + bub["phase"]))
                    pdraw.ellipse([bx - bs, by - bs, bx + bs, by + bs],
                                  outline=(100, 200, 255, min(255, bubble_alpha)),
                                  fill=None)
                    pdraw.ellipse([bx - bs + 2, by - bs + 2, bx - bs + bs // 2, by - bs + bs // 2],
                                  fill=(200, 240, 255, 80))

        # ── Cave: Crystal glow points ──
        if theme_name == "cave":
            for crystal in crystal_data:
                cr_x = crystal["x"]
                cr_y = crystal["y"]
                cr_sz = crystal["size"]
                cr_bright = crystal["brightness"] * (0.5 + 0.5 * math.sin(t * 2 + crystal["phase"]))
                if cr_bright > 0.1:
                    glow_color_cave = tuple(int(c * cr_bright) for c in (120, 200, 255))
                    pdraw.ellipse([cr_x - cr_sz, cr_y - cr_sz, cr_x + cr_sz, cr_y + cr_sz],
                                  fill=glow_color_cave + (int(cr_bright * 60),))
                    pdraw.ellipse([cr_x - cr_sz // 3, cr_y - cr_sz // 3,
                                   cr_x + cr_sz // 3, cr_y + cr_sz // 3],
                                  fill=(200, 240, 255, int(cr_bright * 150)))

        # ── Overworld: Drifting leaves ──
        if theme_name == "overworld":
            for leaf in leaf_data:
                lx = int((leaf["x"] + leaf["speed_x"] * t) % width)
                ly = int((leaf["y"] + leaf["speed_y"] * t) % height)
                ls = leaf["size"]
                pdraw.ellipse([lx - ls, ly - ls // 2, lx + ls, ly + ls // 2],
                              fill=(80, 180, 60, 120))

        # ── Redstone: Circuit line glow ──
        if theme_name == "redstone":
            for spark in spark_data:
                sx = spark["x"]
                sy = spark["y"]
                s_bright = spark["brightness"] * (0.3 + 0.7 * abs(math.sin(t * 3 + spark["phase"])))
                if s_bright > 0.15:
                    sz = int(8 + 6 * s_bright)
                    pdraw.ellipse([sx - sz, sy - sz, sx + sz, sy + sz],
                                  fill=(255, int(40 * s_bright), int(20 * s_bright), int(s_bright * 200)))
                    # Horizontal circuit line
                    for dx in range(-60, 61, 4):
                        nx = sx + dx
                        if 0 <= nx < width:
                            line_bright = s_bright * max(0, 1.0 - abs(dx) / 60)
                            pdraw.point((nx, sy), fill=(255, int(30 * line_bright), 0, int(line_bright * 120)))

        # ── Mob: Flickering red eyes ──
        if theme_name == "mob":
            for eye in eye_data:
                ex, ey = eye["x"], eye["y"]
                blink = 0.5 + 0.5 * math.sin(t * 4 + eye["blink_phase"])
                if blink > 0.3:
                    eye_sz = int(4 + 3 * blink)
                    eye_alpha = int(blink * 200)
                    pdraw.ellipse([ex - eye_sz - 6, ey - eye_sz, ex - 6, ey + eye_sz],
                                  fill=(255, 30, 30, eye_alpha))
                    pdraw.ellipse([ex + 6 - eye_sz, ey - eye_sz, ex + 6 + eye_sz, ey + eye_sz],
                                  fill=(255, 30, 30, eye_alpha))

        # ── Magic: Spiral sparkles ──
        if theme_name == "magic":
            for i in range(20):
                angle = t * 1.5 + i * math.pi * 2 / 20
                spiral_r = 80 + i * 12 + math.sin(t * 2 + i) * 30
                mx = int(cx + spiral_r * math.cos(angle))
                my = int(cy + spiral_r * math.sin(angle) * 0.7)
                if 0 <= mx < width and 0 <= my < height:
                    m_bright = 0.4 + 0.6 * abs(math.sin(t * 3 + i * 0.5))
                    m_sz = int(3 + 4 * m_bright)
                    pdraw.ellipse([mx - m_sz, my - m_sz, mx + m_sz, my + m_sz],
                                  fill=(int(200 * m_bright), int(150 * m_bright), 255, int(m_bright * 180)))

        return np.array(frame_pil)

    return VideoClip(make_frame, duration=duration).set_fps(30)


def load_background_video(
    duration: float,
    topic_theme: str = "overworld",
    width: int = 1080,
    height: int = 1920
) -> VideoClip:
    """
    Loads gameplay footage from assets/gameplay if available and crops it to 9:16 vertical.
    Prioritizes theme-specific backgrounds (e.g. nether_gameplay.mp4 for nether topics).
    Falls back to generic gameplay or procedural animated backdrop.
    """
    ensure_assets_dirs()
    video_extensions = ["*.mp4", "*.mov", "*.mkv", "*.webm", "*.avi"]
    theme = get_theme(topic_theme)

    # Strategy 1: Look for theme-specific gameplay (e.g. nether_gameplay.mp4)
    theme_specific = []
    theme_pattern = f"{topic_theme}_gameplay"
    for ext in video_extensions:
        for f in GAMEPLAY_DIR.glob(ext):
            if theme_pattern.lower() in f.name.lower():
                theme_specific.append(f)

    # Strategy 2: Any gameplay video
    all_videos = []
    for ext in video_extensions:
        all_videos.extend(list(GAMEPLAY_DIR.glob(ext)))

    # Prefer theme-specific, then any available
    candidates = theme_specific if theme_specific else all_videos
    # Exclude raw downloads
    candidates = [v for v in candidates if not v.name.startswith("_raw")]

    if not candidates:
        print(f"[Video Composer] No gameplay videos found. Using evolving animated backdrop for theme: {topic_theme}")
        return create_evolving_backdrop(duration, theme, width, height)

    chosen_video_path = random.choice(candidates)
    label = "theme-matched" if theme_specific else "generic"
    print(f"[Video Composer] Using {label} gameplay background: {chosen_video_path.name} (theme: {topic_theme})")

    try:
        clip = VideoFileClip(str(chosen_video_path))
        if clip.duration <= duration:
            # Loop if clip is shorter than short duration
            clip = clip.loop(duration=duration)
        else:
            # Pick a random starting offset for variety
            max_start = max(0.0, clip.duration - duration - 0.5)
            start_t = random.uniform(0.0, max_start)
            clip = clip.subclip(start_t, start_t + duration)

        clip_w, clip_h = clip.size
        target_aspect = width / height
        clip_aspect = clip_w / clip_h

        # Crop and resize to fill 9:16 (width x height) without black bars
        if clip_aspect > target_aspect:
            # Video is wider than 9:16 -> scale height, crop center width
            clip = clip.resize(height=height)
            new_w, new_h = clip.size
            x_center = new_w // 2
            clip = clip.crop(x1=x_center - width // 2, x2=x_center + width // 2, y1=0, y2=height)
        else:
            # Video is taller or same -> scale width, crop center height
            clip = clip.resize(width=width)
            new_w, new_h = clip.size
            y_center = new_h // 2
            clip = clip.crop(x1=0, x2=width, y1=y_center - height // 2, y2=y_center + height // 2)

        return clip.set_duration(duration)

    except Exception as e:
        print(f"[Video Composer] Warning: Could not load gameplay video ({e}). Falling back to evolving backdrop.")
        return create_evolving_backdrop(duration, theme, width, height)


def render_caption_frame(
    chunk_text: str,
    t_in_chunk: float,
    chunk_duration: float,
    theme: dict,
    width: int = 1080,
    font_size: int = 68
) -> Image.Image:
    """
    Renders professional captions that appear BEHIND the character.
    - Pop-in with scale bounce
    - Word-by-word highlight
    - Glow + shadow
    - Positioned for BEHIND-character layout
    """
    canvas_h = 350
    canvas = Image.new("RGBA", (width, canvas_h), (0, 0, 0, 0))

    # Animation timing
    pop_in = 0.15
    pop_out = 0.12

    if t_in_chunk < pop_in:
        p = t_in_chunk / pop_in
        scale = 0.5 + 0.5 * p + 0.25 * math.sin(p * math.pi)
        alpha = min(255, int(p * 350))
    elif t_in_chunk > (chunk_duration - pop_out):
        p = (chunk_duration - t_in_chunk) / pop_out
        scale = max(0.4, p)
        alpha = max(0, int(p * 255))
    else:
        scale = 1.0 + 0.02 * math.sin(t_in_chunk * 5.0)
        alpha = 255

    float_y = math.sin(t_in_chunk * 3.5) * 4

    actual_size = max(20, int(font_size * scale))
    font = get_font(actual_size)
    draw = ImageDraw.Draw(canvas)

    # Don't uppercase Hindi text
    text = chunk_text

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception as e:
        print(f"[Video Composer] textbbox failed, using fallback: {e}")
        text_w, text_h = 400, 60

    # Ensure text fits within width
    if text_w > width - 60:
        actual_size = max(20, int(actual_size * (width - 60) / text_w))
        font = get_font(actual_size)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception as e:
            print(f"[Video Composer] textbbox retry failed: {e}")
            pass

    x = (width - text_w) // 2
    y = int((canvas_h - text_h) // 2 + float_y)

    stroke_w = max(4, int(7 * scale))

    # Semi-transparent dark background pill behind text
    pill_pad_x, pill_pad_y = 30, 15
    pill_alpha = int(alpha * 0.5)
    draw.rounded_rectangle(
        [x - pill_pad_x, y - pill_pad_y, x + text_w + pill_pad_x, y + text_h + pill_pad_y],
        radius=20,
        fill=(0, 0, 0, pill_alpha)
    )

    # Glow layers
    glow_c = theme["subtitle_glow"] + (max(0, alpha // 4),)
    for off in range(2, 0, -1):
        draw.text((x, y), text, font=font, fill=glow_c,
                  stroke_width=stroke_w + off * 3, stroke_fill=glow_c)

    # Shadow
    shadow_a = max(0, int(alpha * 0.6))
    draw.text((x + 3, y + 4), text, font=font,
              fill=(0, 0, 0, shadow_a), stroke_width=stroke_w, stroke_fill=(0, 0, 0, shadow_a))

    # Main text
    fill_c = theme["subtitle_fill"] + (alpha,)
    draw.text((x, y), text, font=font, fill=fill_c,
              stroke_width=stroke_w, stroke_fill=(0, 0, 0, alpha))

    return canvas


def create_watermark_image(text: str, opacity: float = 0.85) -> Image.Image:
    """Creates a sleek glassmorphism pill watermark badge."""
    font = get_ascii_font(36)
    dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad_x, pad_y = 28, 16
    bw, bh = tw + pad_x * 2, th + pad_y * 2

    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    alpha_bg = int(140 * opacity)
    draw.rounded_rectangle([0, 0, bw, bh], radius=bh // 2,
                           fill=(10, 15, 25, alpha_bg),
                           outline=(255, 255, 255, int(80 * opacity)), width=2)
    draw.text((pad_x + 1, pad_y + 1), text, font=font, fill=(0, 0, 0, int(180 * opacity)))
    draw.text((pad_x, pad_y), text, font=font, fill=(255, 255, 255, int(250 * opacity)))

    return badge


def pil_to_image_clip(pil_img: Image.Image, duration: float = 1.0) -> ImageClip:
    arr = np.array(pil_img)
    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = arr[:, :, :3]
        alpha = (arr[:, :, 3] / 255.0).astype(np.float32)
        mask = ImageClip(alpha, ismask=True).set_duration(duration)
        clip = ImageClip(rgb).set_duration(duration).set_mask(mask)
        return clip
    return ImageClip(arr).set_duration(duration)


def create_full_short_video(
    voiceover_path: str,
    subtitle_chunks: List[Dict[str, Any]],
    output_mp4_path: str,
    custom_username: Optional[str] = None,
    topic_theme: str = "overworld"
) -> str:
    """
    Assembles YouTube Short with layering order:
    1. Evolving animated background (non-looping)
    2. Professional captions (BEHIND character)
    3. Character avatar (CENTER, large, IN FRONT of text)
    4. Watermark (top)
    """
    config = load_config()
    vid_cfg = config.get("video", {})
    chan_cfg = config.get("channel", {})
    player_cfg = config.get("player", {})

    width = vid_cfg.get("width", 1080)
    height = vid_cfg.get("height", 1920)
    fps = vid_cfg.get("fps", 30)

    theme = get_theme(topic_theme)
    print(f"[Video Composer] Using theme: {topic_theme}")

    # 1. Audio
    voice_audio = AudioFileClip(voiceover_path)
    total_duration = voice_audio.duration + 0.8

    ensure_assets_dirs()
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    audio_tracks = [voice_audio]

    if music_files:
        bg_music_path = random.choice(music_files)
        bg_music = AudioFileClip(str(bg_music_path))
        if bg_music.duration < total_duration:
            bg_music = bg_music.loop(duration=total_duration)
        else:
            bg_music = bg_music.subclip(0, total_duration)
        music_vol = vid_cfg.get("music_volume", 0.12)
        duck_enabled = vid_cfg.get("duck_music_under_speech", False)
        if duck_enabled:
            music_vol = music_vol * 0.5
        bg_music = bg_music.volumex(music_vol)
        audio_tracks.append(bg_music)

    final_audio = CompositeAudioClip(audio_tracks).set_duration(total_duration)

    # 2. Background video (Gameplay video from assets/gameplay or evolving backdrop)
    bg_video = load_background_video(total_duration, topic_theme, width, height)
    video_layers = [bg_video]

    # 3. Captions BEHIND character (added BEFORE avatar layer)
    caption_y = int(height * config.get("captions", {}).get("position_y_ratio", 0.38))
    font_size = config.get("captions", {}).get("font_size", 68)

    for chunk in subtitle_chunks:
        c_start = max(0.0, chunk["start"])
        if c_start >= total_duration:
            continue
        c_end = min(total_duration, chunk["end"] + 0.25)
        c_duration = max(0.1, c_end - c_start)

        def make_sub_factory(text, dur, th):
            _cache = {}
            def _render(t):
                t_key = round(t, 4)
                if t_key not in _cache:
                    _cache[t_key] = np.array(render_caption_frame(text, t, dur, th, width, font_size))
                return _cache[t_key]
            def rgb_fn(t):
                return _render(t)[:, :, :3]
            def mask_fn(t):
                return (_render(t)[:, :, 3] / 255.0).astype(np.float32)
            return rgb_fn, mask_fn

        sub_rgb, sub_mask = make_sub_factory(chunk["text"], c_duration, theme)

        mask_clip = VideoClip(sub_mask, duration=c_duration, ismask=True)
        sub_clip = (
            VideoClip(sub_rgb, duration=c_duration)
            .set_mask(mask_clip)
            .set_start(c_start)
            .set_position(("center", caption_y))
        )
        video_layers.append(sub_clip)

    # 4. Character avatar - CENTERED, large, IN FRONT of text
    avatar_username = custom_username or player_cfg.get("minecraft_username", "Anil_playz29")
    avatar_base_img = get_player_avatar(avatar_username)

    avatar_scale = player_cfg.get("avatar_scale", 0.28)
    avatar_w = int(width * avatar_scale)
    avatar_h = int(avatar_base_img.height * (avatar_w / avatar_base_img.width))
    avatar_resized = avatar_base_img.resize((avatar_w, avatar_h), Image.BICUBIC)

    anim_type = player_cfg.get("avatar_animation", "talking_bob")

    avatar_position = player_cfg.get("avatar_position", "center")
    if avatar_position == "bottom_left":
        avatar_x = 40
        avatar_y = height - avatar_h - 200
    elif avatar_position == "bottom_right":
        avatar_x = width - avatar_w - 40
        avatar_y = height - avatar_h - 200
    elif avatar_position == "top_center":
        avatar_x = (width - avatar_w) // 2
        avatar_y = 150
    elif avatar_position == "center":
        avatar_x = (width - avatar_w) // 2
        avatar_y = int(height * 0.45) - avatar_h // 2
    else:
        avatar_x = (width - avatar_w) // 2
        avatar_y = int(height * 0.45) - avatar_h // 2

    _avatar_cache = {}
    def _render_avatar(t):
        t_key = round(t, 4)
        if t_key not in _avatar_cache:
            frame = generate_avatar_frame(avatar_resized, t, anim_type)
            _avatar_cache[t_key] = np.array(frame)
        return _avatar_cache[t_key]

    def make_avatar_rgb(t):
        arr = _render_avatar(t)
        if arr.ndim == 3 and arr.shape[2] == 4:
            return arr[:, :, :3]
        return arr

    def make_avatar_mask(t):
        arr = _render_avatar(t)
        if arr.ndim == 3 and arr.shape[2] == 4:
            return (arr[:, :, 3] / 255.0).astype(np.float32)
        return np.ones((arr.shape[0], arr.shape[1]), dtype=np.float32)

    avatar_mask = VideoClip(make_avatar_mask, duration=total_duration, ismask=True)
    avatar_clip = (
        VideoClip(make_avatar_rgb, duration=total_duration)
        .set_mask(avatar_mask)
        .set_position((avatar_x, avatar_y))
    )
    video_layers.append(avatar_clip)  # Added AFTER captions = renders IN FRONT

    # 5. Watermark on top
    watermark_text = chan_cfg.get("watermark_text", "@Anil-Patel-29")
    opacity = chan_cfg.get("watermark_opacity", 0.85)
    watermark_img = create_watermark_image(watermark_text, opacity)
    wm_position = chan_cfg.get("watermark_position", "top_right")
    if wm_position == "top_right":
        wm_pos = (width - watermark_img.width - 20, 80)
    elif wm_position == "top_left":
        wm_pos = (20, 80)
    elif wm_position == "bottom_center":
        wm_pos = ((width - watermark_img.width) // 2, height - watermark_img.height - 80)
    else:
        wm_pos = ((width - watermark_img.width) // 2, 80)  # top_center fallback
    wm_clip = pil_to_image_clip(watermark_img, total_duration).set_position(wm_pos)
    video_layers.append(wm_clip)

    # 6. Render
    print(f"[Video Composer] Rendering final Short ({total_duration:.1f}s, {width}x{height} @ {fps}fps)...")
    final_video = CompositeVideoClip(video_layers, size=(width, height)).set_audio(final_audio).set_duration(total_duration)

    Path(output_mp4_path).parent.mkdir(parents=True, exist_ok=True)

    final_video.write_videofile(
        output_mp4_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        logger=None
    )

    print(f"[Video Composer] Successfully generated video: {output_mp4_path}")
    return output_mp4_path
