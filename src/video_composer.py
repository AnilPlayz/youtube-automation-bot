"""Video Composition Engine for Hindi Minecraft Facts Shorts.
Features: Animated popup subtitles, dynamic themed backgrounds, player avatar overlay, watermark.
"""

import math
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

# ── Theme color palettes keyed by topic_theme ──
THEME_PALETTES = {
    "nether": {
        "bg_dark": (45, 10, 10),
        "bg_mid": (80, 20, 15),
        "bg_light": (120, 35, 20),
        "accent": (255, 100, 30),
        "glow": (255, 60, 20),
        "particle": (255, 180, 50),
        "subtitle_fill": (255, 200, 60),
        "subtitle_highlight": (255, 80, 30),
    },
    "end": {
        "bg_dark": (10, 5, 30),
        "bg_mid": (25, 12, 60),
        "bg_light": (50, 25, 90),
        "accent": (200, 120, 255),
        "glow": (180, 80, 255),
        "particle": (220, 180, 255),
        "subtitle_fill": (220, 180, 255),
        "subtitle_highlight": (140, 255, 200),
    },
    "overworld": {
        "bg_dark": (15, 35, 15),
        "bg_mid": (30, 65, 30),
        "bg_light": (50, 100, 45),
        "accent": (100, 220, 80),
        "glow": (80, 200, 60),
        "particle": (180, 255, 100),
        "subtitle_fill": (255, 230, 0),
        "subtitle_highlight": (0, 255, 128),
    },
    "ocean": {
        "bg_dark": (5, 20, 50),
        "bg_mid": (10, 40, 90),
        "bg_light": (20, 70, 130),
        "accent": (50, 180, 255),
        "glow": (30, 150, 255),
        "particle": (100, 220, 255),
        "subtitle_fill": (100, 240, 255),
        "subtitle_highlight": (255, 220, 80),
    },
    "cave": {
        "bg_dark": (18, 18, 25),
        "bg_mid": (35, 32, 45),
        "bg_light": (55, 50, 70),
        "accent": (120, 200, 255),
        "glow": (80, 180, 240),
        "particle": (200, 220, 255),
        "subtitle_fill": (200, 230, 255),
        "subtitle_highlight": (255, 200, 80),
    },
    "mob": {
        "bg_dark": (25, 12, 12),
        "bg_mid": (50, 25, 30),
        "bg_light": (80, 40, 45),
        "accent": (255, 60, 80),
        "glow": (255, 40, 60),
        "particle": (255, 150, 100),
        "subtitle_fill": (255, 100, 120),
        "subtitle_highlight": (255, 255, 80),
    },
    "redstone": {
        "bg_dark": (30, 8, 8),
        "bg_mid": (60, 15, 15),
        "bg_light": (100, 25, 25),
        "accent": (255, 0, 0),
        "glow": (255, 50, 50),
        "particle": (255, 120, 80),
        "subtitle_fill": (255, 80, 80),
        "subtitle_highlight": (255, 255, 100),
    },
    "magic": {
        "bg_dark": (20, 10, 40),
        "bg_mid": (40, 20, 80),
        "bg_light": (70, 35, 120),
        "accent": (180, 100, 255),
        "glow": (150, 80, 255),
        "particle": (255, 150, 255),
        "subtitle_fill": (255, 180, 255),
        "subtitle_highlight": (100, 255, 200),
    },
}

def ensure_assets_dirs():
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

def get_theme(topic_theme: str) -> dict:
    """Get color palette for a given topic theme."""
    return THEME_PALETTES.get(topic_theme, THEME_PALETTES["overworld"])

def get_font(size: int = 70) -> ImageFont.ImageFont:
    """Load bold font for subtitles. Tries Hindi-capable fonts first."""
    # Check custom font files in fonts directory first
    for ext in ["*.ttf", "*.otf"]:
        for font_file in FONTS_DIR.glob(ext):
            try:
                return ImageFont.truetype(str(font_file), size)
            except Exception:
                pass

    # Try common system fonts that support Hindi (Devanagari)
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\NirmalaB.ttf",        # Nirmala UI Bold (Hindi support)
        "C:\\Windows\\Fonts\\Nirmala.ttf",         # Nirmala UI (Hindi support)
        "C:\\Windows\\Fonts\\mangal.ttf",          # Mangal (Hindi)
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\impact.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "arial.ttf"
    ]
    for c in candidates:
        try:
            f = ImageFont.truetype(c, size)
            # Test if the font can render Hindi characters
            f.getbbox("क")
            return f
        except Exception:
            continue

    return ImageFont.load_default()


def create_themed_backdrop(duration: float, theme: dict, width: int = 1080, height: int = 1920) -> VideoClip:
    """
    Creates an animated themed Minecraft-style backdrop with floating particles,
    gradient background, and dynamic grid that matches the script topic.
    """
    print(f"[Video Composer] Generating themed dynamic backdrop...")

    bg_dark = theme["bg_dark"]
    bg_mid = theme["bg_mid"]
    bg_light = theme["bg_light"]
    accent = theme["accent"]
    glow = theme["glow"]
    particle_color = theme["particle"]

    # Pre-render the gradient background with themed grid
    grid_size = 80
    canvas_w = width + grid_size * 4
    canvas_h = height + grid_size * 4

    base_img = Image.new("RGB", (canvas_w, canvas_h), bg_dark)
    draw = ImageDraw.Draw(base_img)

    # Draw gradient from top to bottom
    for y in range(canvas_h):
        ratio = y / canvas_h
        r = int(bg_dark[0] * (1 - ratio) + bg_mid[0] * ratio)
        g = int(bg_dark[1] * (1 - ratio) + bg_mid[1] * ratio)
        b = int(bg_dark[2] * (1 - ratio) + bg_mid[2] * ratio)
        draw.line([(0, y), (canvas_w, y)], fill=(r, g, b))

    # Draw themed grid blocks
    for y in range(0, canvas_h, grid_size):
        for x in range(0, canvas_w, grid_size):
            is_even = ((x // grid_size) + (y // grid_size)) % 2 == 0
            if is_even:
                c = bg_mid
            else:
                c = (
                    min(255, bg_dark[0] + 8),
                    min(255, bg_dark[1] + 8),
                    min(255, bg_dark[2] + 8),
                )
            # Semi-transparent block overlay
            block_alpha = random.randint(30, 80)
            draw.rectangle(
                [x + 2, y + 2, x + grid_size - 4, y + grid_size - 4],
                fill=c, outline=(
                    min(255, c[0] + 15),
                    min(255, c[1] + 15),
                    min(255, c[2] + 15),
                ), width=1
            )

    # Pre-render floating particles (static positions, animated via offset)
    num_particles = 30
    particles = []
    for _ in range(num_particles):
        px = random.randint(0, width)
        py = random.randint(0, height)
        psize = random.randint(3, 12)
        pspeed = random.uniform(20, 80)
        pdrift = random.uniform(-15, 15)
        pbrightness = random.uniform(0.4, 1.0)
        particles.append((px, py, psize, pspeed, pdrift, pbrightness))

    base_np = np.array(base_img)

    def make_frame(t):
        # Scrolling background
        offset_y = int((t * 60) % grid_size)
        offset_x = int((t * 20) % grid_size)
        frame_rgb = base_np[offset_y: offset_y + height, offset_x: offset_x + width].copy()

        # Draw floating particles
        frame_pil = Image.fromarray(frame_rgb)
        pdraw = ImageDraw.Draw(frame_pil)

        for (px, py, psize, pspeed, pdrift, pbright) in particles:
            # Animate particles floating upward
            anim_y = (py - t * pspeed) % height
            anim_x = px + math.sin(t * 1.5 + pdrift) * 30

            pc = (
                int(particle_color[0] * pbright),
                int(particle_color[1] * pbright),
                int(particle_color[2] * pbright),
            )
            # Glow effect: larger semi-transparent circle + bright center
            glow_size = psize + 6
            gc = (
                int(glow[0] * pbright * 0.3),
                int(glow[1] * pbright * 0.3),
                int(glow[2] * pbright * 0.3),
            )
            pdraw.ellipse(
                [anim_x - glow_size, anim_y - glow_size, anim_x + glow_size, anim_y + glow_size],
                fill=gc
            )
            pdraw.ellipse(
                [anim_x - psize, anim_y - psize, anim_x + psize, anim_y + psize],
                fill=pc
            )

        # Pulsing vignette overlay
        pulse = 0.6 + 0.1 * math.sin(t * 2.0)
        result = np.array(frame_pil)

        # Apply vignette darkening at edges
        y_coords, x_coords = np.ogrid[:height, :width]
        cx, cy = width / 2, height / 2
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        vignette = 1.0 - (dist / max_dist) * (0.5 * pulse)
        vignette = np.clip(vignette, 0.3, 1.0)

        result = (result * vignette[:, :, np.newaxis]).astype(np.uint8)
        return result

    return VideoClip(make_frame, duration=duration).set_fps(30)


def load_background_video(duration: float, topic_theme: str = "overworld", width: int = 1080, height: int = 1920) -> VideoClip:
    """Load gameplay video or generate themed backdrop."""
    ensure_assets_dirs()
    video_files = list(GAMEPLAY_DIR.glob("*.mp4")) + list(GAMEPLAY_DIR.glob("*.mov")) + list(GAMEPLAY_DIR.glob("*.mkv"))

    if not video_files:
        print("[Video Composer] No gameplay videos found. Using themed dynamic backdrop.")
        theme = get_theme(topic_theme)
        return create_themed_backdrop(duration, theme, width, height)

    chosen_video_path = random.choice(video_files)
    print(f"[Video Composer] Slicing gameplay background from: {chosen_video_path.name}")

    try:
        clip = VideoFileClip(str(chosen_video_path))
        if clip.duration <= duration:
            clip = clip.loop(duration=duration)
        else:
            max_start = max(0, clip.duration - duration - 1)
            start_t = random.uniform(0, max_start)
            clip = clip.subclip(start_t, start_t + duration)

        clip_w, clip_h = clip.size
        target_aspect = width / height
        clip_aspect = clip_w / clip_h

        if clip_aspect > target_aspect:
            clip = clip.resize(height=height)
            new_w, new_h = clip.size
            x_center = new_w / 2
            clip = clip.crop(x1=x_center - width / 2, x2=x_center + width / 2, y1=0, y2=height)
        else:
            clip = clip.resize(width=width)
            new_w, new_h = clip.size
            y_center = new_h / 2
            clip = clip.crop(x1=0, x2=width, y1=y_center - height / 2, y2=y_center + height / 2)

        return clip.set_duration(duration)

    except Exception as e:
        print(f"[Video Composer] Error loading video ({e}). Falling back to themed backdrop.")
        theme = get_theme(topic_theme)
        return create_themed_backdrop(duration, theme, width, height)


def render_animated_subtitle_frame(
    chunk_text: str,
    t_in_chunk: float,
    chunk_duration: float,
    theme: dict,
    width: int = 1080,
    font_size: int = 74
) -> Image.Image:
    """
    Renders a single frame of an animated popup subtitle with:
    - Scale-in bounce effect on appear
    - Gentle float/pulse during display
    - Scale-out on disappear
    - Glowing themed colors
    """
    canvas_h = 300
    canvas = Image.new("RGBA", (width, canvas_h), (0, 0, 0, 0))

    # Animation timing
    pop_in_duration = 0.15
    pop_out_duration = 0.12
    t_ratio = t_in_chunk / max(chunk_duration, 0.01)

    # Scale animation
    if t_in_chunk < pop_in_duration:
        # Bounce-in: overshoot then settle
        p = t_in_chunk / pop_in_duration
        scale = 1.0 + 0.3 * math.sin(p * math.pi)  # Overshoot to 1.3x then settle
        alpha = min(255, int(p * 300))
    elif t_in_chunk > (chunk_duration - pop_out_duration):
        # Quick fade out
        p = (chunk_duration - t_in_chunk) / pop_out_duration
        scale = max(0.5, p)
        alpha = max(0, int(p * 255))
    else:
        # Steady with subtle pulse
        scale = 1.0 + 0.03 * math.sin(t_in_chunk * 6.0)
        alpha = 255

    # Floating Y offset (gentle bob)
    float_y = math.sin(t_in_chunk * 4.0) * 5

    actual_font_size = max(20, int(font_size * scale))
    font = get_font(actual_font_size)

    draw = ImageDraw.Draw(canvas)
    text_upper = chunk_text.upper()

    # Get text dimensions
    try:
        bbox = draw.textbbox((0, 0), text_upper, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        text_w, text_h = 400, 60

    x = (width - text_w) // 2
    y = int((canvas_h - text_h) // 2 + float_y)

    fill_color = theme["subtitle_fill"] + (alpha,)
    stroke_color = (0, 0, 0, alpha)
    stroke_width = max(4, int(8 * scale))

    # Glow behind text
    glow_color = theme["glow"] + (max(0, alpha // 3),)
    for offset in range(3, 0, -1):
        draw.text(
            (x, y),
            text_upper,
            font=font,
            fill=glow_color,
            stroke_width=stroke_width + offset * 3,
            stroke_fill=glow_color
        )

    # Drop shadow
    shadow_alpha = max(0, int(alpha * 0.7))
    draw.text(
        (x + 4, y + 5),
        text_upper,
        font=font,
        fill=(0, 0, 0, shadow_alpha),
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, shadow_alpha)
    )

    # Main text
    draw.text(
        (x, y),
        text_upper,
        font=font,
        fill=fill_color,
        stroke_width=stroke_width,
        stroke_fill=stroke_color
    )

    return canvas


def create_watermark_image(text: str, opacity: float = 0.85) -> Image.Image:
    """Creates a sleek glassmorphism pill watermark badge."""
    font = get_font(36)
    dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad_x, pad_y = 28, 16
    bw, bh = tw + pad_x * 2, th + pad_y * 2

    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    alpha_bg = int(140 * opacity)
    draw.rounded_rectangle([0, 0, bw, bh], radius=bh // 2, fill=(10, 15, 25, alpha_bg), outline=(255, 255, 255, int(80 * opacity)), width=2)

    draw.text((pad_x + 1, pad_y + 1), text, font=font, fill=(0, 0, 0, int(180 * opacity)))
    draw.text((pad_x, pad_y), text, font=font, fill=(255, 255, 255, int(250 * opacity)))

    return badge


def pil_to_image_clip(pil_img: Image.Image, duration: float = 1.0) -> ImageClip:
    """Converts a PIL RGBA image to a MoviePy ImageClip with proper alpha transparency mask."""
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
    Assembles the complete YouTube Short MP4 video with:
    - Themed dynamic background matching script topic
    - Animated popup subtitles with bounce/glow effects
    - Player avatar overlay
    - Glassmorphism watermark
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

    # 1. Load Audio
    voice_audio = AudioFileClip(voiceover_path)
    total_duration = voice_audio.duration + 0.8

    # 2. Background Music
    ensure_assets_dirs()
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    audio_tracks = [voice_audio]

    if music_files:
        bg_music_path = random.choice(music_files)
        print(f"[Video Composer] Adding background music: {bg_music_path.name}")
        bg_music = AudioFileClip(str(bg_music_path))
        if bg_music.duration < total_duration:
            bg_music = bg_music.loop(duration=total_duration)
        else:
            bg_music = bg_music.subclip(0, total_duration)

        music_vol = vid_cfg.get("music_volume", 0.12)
        bg_music = bg_music.volumex(music_vol)
        audio_tracks.append(bg_music)

    final_audio = CompositeAudioClip(audio_tracks).set_duration(total_duration)

    # 3. Themed Background Video
    bg_video = load_background_video(total_duration, topic_theme, width, height)

    video_layers = [bg_video]

    # 4. Watermark Layer
    watermark_text = chan_cfg.get("watermark_text", "@Anil-Patel-29")
    opacity = chan_cfg.get("watermark_opacity", 0.85)
    watermark_img = create_watermark_image(watermark_text, opacity)

    pos_setting = chan_cfg.get("watermark_position", "top_right")
    if pos_setting == "top_left":
        wm_pos = (50, 100)
    elif pos_setting == "bottom_center":
        wm_pos = ((width - watermark_img.width) // 2, height - 160)
    else:
        wm_pos = (width - watermark_img.width - 50, 100)

    wm_clip = pil_to_image_clip(watermark_img, total_duration).set_position(wm_pos)
    video_layers.append(wm_clip)

    # 5. Player Avatar Overlay Layer
    avatar_username = custom_username or player_cfg.get("minecraft_username", "Anil_playz29")
    avatar_base_img = get_player_avatar(avatar_username)

    avatar_scale = player_cfg.get("avatar_scale", 0.28)
    avatar_w = int(width * avatar_scale)
    avatar_h = int(avatar_base_img.height * (avatar_w / avatar_base_img.width))
    avatar_resized = avatar_base_img.resize((avatar_w, avatar_h), Image.BICUBIC)

    anim_type = player_cfg.get("avatar_animation", "talking_bob")

    avatar_pos_cfg = player_cfg.get("avatar_position", "bottom_left")
    if avatar_pos_cfg == "bottom_right":
        avatar_xy = (width - avatar_w - 40, height - avatar_h - 180)
    else:
        avatar_xy = (40, height - avatar_h - 180)

    def make_avatar_rgb(t):
        frame = generate_avatar_frame(avatar_resized, t, anim_type)
        arr = np.array(frame)
        if arr.ndim == 3 and arr.shape[2] == 4:
            return arr[:, :, :3]
        return arr

    def make_avatar_mask(t):
        frame = generate_avatar_frame(avatar_resized, t, anim_type)
        arr = np.array(frame)
        if arr.ndim == 3 and arr.shape[2] == 4:
            return (arr[:, :, 3] / 255.0).astype(np.float32)
        return np.ones((arr.shape[0], arr.shape[1]), dtype=np.float32)

    avatar_mask = VideoClip(make_avatar_mask, duration=total_duration, ismask=True)
    avatar_clip = (
        VideoClip(make_avatar_rgb, duration=total_duration)
        .set_mask(avatar_mask)
        .set_position(avatar_xy)
    )
    video_layers.append(avatar_clip)

    # 6. Animated Popup Subtitle Overlay Clips
    sub_y = int(height * config.get("captions", {}).get("position_y_ratio", 0.65))
    font_size = config.get("captions", {}).get("font_size", 72)

    for chunk in subtitle_chunks:
        c_start = max(0.0, chunk["start"])
        c_end = min(total_duration, chunk["end"] + 0.25)
        c_duration = max(0.1, c_end - c_start)

        # Create animated subtitle as a VideoClip (frame-by-frame)
        def make_sub_frame_factory(text, dur, th):
            def make_sub_rgb(t):
                img = render_animated_subtitle_frame(text, t, dur, th, width, font_size)
                arr = np.array(img)
                return arr[:, :, :3]
            return make_sub_rgb

        def make_sub_mask_factory(text, dur, th):
            def make_sub_mask(t):
                img = render_animated_subtitle_frame(text, t, dur, th, width, font_size)
                arr = np.array(img)
                return (arr[:, :, 3] / 255.0).astype(np.float32)
            return make_sub_mask

        sub_rgb_fn = make_sub_frame_factory(chunk["text"], c_duration, theme)
        sub_mask_fn = make_sub_mask_factory(chunk["text"], c_duration, theme)

        sub_mask_clip = VideoClip(sub_mask_fn, duration=c_duration, ismask=True)
        sub_clip = (
            VideoClip(sub_rgb_fn, duration=c_duration)
            .set_mask(sub_mask_clip)
            .set_start(c_start)
            .set_position(("center", sub_y))
        )
        video_layers.append(sub_clip)

    # 7. Render Final Video
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
        logger=None
    )

    print(f"[Video Composer] Successfully generated video: {output_mp4_path}")
    return output_mp4_path
