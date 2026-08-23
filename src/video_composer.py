"""Video Composition Engine for Minecraft Facts Shorts.
Combines 9:16 gameplay video, animated subtitles, player avatar overlay, watermark, and ducked audio.
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

def ensure_assets_dirs():
    GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int = 70) -> ImageFont.ImageFont:
    """Load bold font for subtitles."""
    # Check custom font files in fonts directory first
    for ext in ["*.ttf", "*.otf"]:
        for font_file in FONTS_DIR.glob(ext):
            try:
                return ImageFont.truetype(str(font_file), size)
            except Exception:
                pass

    # Try common system fonts across Windows/Linux/Mac
    candidates = [
        "C:\\Windows\\Fonts\\arialbd.ttf",     # Arial Bold
        "C:\\Windows\\Fonts\\impact.ttf",      # Impact
        "C:\\Windows\\Fonts\\seguiemj.ttf",    # Segoe UI
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Impact.ttf",
        "arial.ttf"
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue

    return ImageFont.load_default()

def create_synthetic_gameplay_clip(duration: float, width: int = 1080, height: int = 1920) -> VideoClip:
    """
    Generates an animated procedural Minecraft-style dynamic gradient/grid background
    if no user gameplay video is placed in assets/gameplay/.
    """
    print("[Video Composer] Generating dynamic Minecraft themed backdrop...")

    def make_frame(t):
        img = Image.new("RGB", (width, height), (15, 20, 35))
        draw = ImageDraw.Draw(img)

        # Draw moving Minecraft block grid
        grid_size = 80
        offset_y = int((t * 120) % grid_size)
        offset_x = int((t * 40) % grid_size)

        for y in range(-grid_size, height + grid_size, grid_size):
            for x in range(-grid_size, width + grid_size, grid_size):
                real_x = x - offset_x
                real_y = y + offset_y
                # Subtle checkerboard
                is_even = ((x // grid_size) + (y // grid_size)) % 2 == 0
                c = (25, 38, 55) if is_even else (20, 30, 45)
                draw.rectangle([real_x, real_y, real_x + grid_size - 2, real_y + grid_size - 2], fill=c)

        # Ambient floating particle orbs
        for i in range(12):
            seed = i * 137
            px = int((seed * 37 + t * (40 + (i % 5) * 15)) % width)
            py = int((height - (seed * 83 + t * (60 + (i % 4) * 20)) % height))
            radius = 12 + (i % 8)
            draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=(50, 180, 255, 60))

        return np.array(img)

    return VideoClip(make_frame, duration=duration).set_fps(30)

def load_background_video(duration: float, width: int = 1080, height: int = 1920) -> VideoClip:
    """
    Finds a gameplay video in assets/gameplay/ and slices a random section matching duration,
    resizing and center-cropping to 9:16 (1080x1920).
    """
    ensure_assets_dirs()
    video_files = list(GAMEPLAY_DIR.glob("*.mp4")) + list(GAMEPLAY_DIR.glob("*.mov")) + list(GAMEPLAY_DIR.glob("*.mkv"))

    if not video_files:
        print("[Video Composer] No gameplay videos found in assets/gameplay/. Using dynamic backdrop.")
        return create_synthetic_gameplay_clip(duration, width, height)

    chosen_video_path = random.choice(video_files)
    print(f"[Video Composer] Slicing gameplay background from: {chosen_video_path.name}")

    try:
        clip = VideoFileClip(str(chosen_video_path))
        if clip.duration <= duration:
            # Loop clip if shorter
            clip = clip.loop(duration=duration)
        else:
            # Pick a random start point
            max_start = max(0, clip.duration - duration - 1)
            start_t = random.uniform(0, max_start)
            clip = clip.subclip(start_t, start_t + duration)

        # Scale and crop to 1080x1920 (9:16)
        clip_w, clip_h = clip.size
        target_aspect = width / height  # 9/16 = 0.5625
        clip_aspect = clip_w / clip_h

        if clip_aspect > target_aspect:
            # Wider than 9:16 -> scale height, crop width
            clip = clip.resize(height=height)
            new_w, new_h = clip.size
            x_center = new_w / 2
            clip = clip.crop(x1=x_center - width / 2, x2=x_center + width / 2, y1=0, y2=height)
        else:
            # Taller -> scale width, crop height
            clip = clip.resize(width=width)
            new_w, new_h = clip.size
            y_center = new_h / 2
            clip = clip.crop(x1=0, x2=width, y1=y_center - height / 2, y2=y_center + height / 2)

        return clip.set_duration(duration)

    except Exception as e:
        print(f"[Video Composer] Error loading video file ({e}). Falling back to synthetic backdrop.")
        return create_synthetic_gameplay_clip(duration, width, height)

def render_subtitle_image(
    chunk_text: str,
    active_word: Optional[str] = None,
    width: int = 1080,
    font_size: int = 74
) -> Image.Image:
    """
    Renders high-impact styled text image with thick black borders, glowing fill,
    and highlighted active word for Shorts retention.
    """
    canvas = Image.new("RGBA", (width, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = get_font(font_size)

    words = chunk_text.upper().split()
    total_text = " ".join(words)

    # Get bounding box
    bbox = draw.textbbox((0, 0), total_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    start_x = (width - text_w) // 2
    start_y = (canvas.height - text_h) // 2

    # Draw words with drop shadow and outline
    curr_x = start_x
    space_w = draw.textlength(" ", font=font)

    for w in words:
        is_highlight = (active_word and w.lower() == active_word.lower())
        fill_color = (0, 255, 128, 255) if is_highlight else (255, 230, 0, 255)
        stroke_color = (0, 0, 0, 255)
        stroke_width = 8

        # Shadow
        draw.text(
            (curr_x + 5, start_y + 6),
            w,
            font=font,
            fill=(0, 0, 0, 200),
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0, 200)
        )

        # Main text with bold stroke
        draw.text(
            (curr_x, start_y),
            w,
            font=font,
            fill=fill_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color
        )

        curr_x += int(draw.textlength(w, font=font) + space_w)

    return canvas

def create_watermark_image(text: str, opacity: float = 0.85) -> Image.Image:
    """Creates a sleek glassmorphism pill watermark badge with text/handle."""
    font = get_font(36)
    # Estimate size
    dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad_x, pad_y = 28, 16
    bw, bh = tw + pad_x * 2, th + pad_y * 2

    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    # Semi-transparent pill background
    alpha_bg = int(140 * opacity)
    draw.rounded_rectangle([0, 0, bw, bh], radius=bh // 2, fill=(10, 15, 25, alpha_bg), outline=(255, 255, 255, int(80 * opacity)), width=2)

    # Watermark text with subtle shadow
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
    custom_username: Optional[str] = None
) -> str:
    """
    Assembles the complete YouTube Short MP4 video.
    """
    config = load_config()
    vid_cfg = config.get("video", {})
    chan_cfg = config.get("channel", {})
    player_cfg = config.get("player", {})

    width = vid_cfg.get("width", 1080)
    height = vid_cfg.get("height", 1920)
    fps = vid_cfg.get("fps", 30)

    # 1. Load Audio
    voice_audio = AudioFileClip(voiceover_path)
    total_duration = voice_audio.duration + 0.8  # Add 0.8s tail cushion

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

    # 3. Background Video
    bg_video = load_background_video(total_duration, width, height)

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
    else:  # top_right
        wm_pos = (width - watermark_img.width - 50, 100)

    wm_clip = pil_to_image_clip(watermark_img, total_duration).set_position(wm_pos)
    video_layers.append(wm_clip)

    # 5. Player Avatar Overlay Layer
    avatar_username = custom_username or player_cfg.get("minecraft_username", "Anil_playz29")
    avatar_base_img = get_player_avatar(avatar_username)

    # Scale avatar to configured size
    avatar_scale = player_cfg.get("avatar_scale", 0.28)
    avatar_w = int(width * avatar_scale)
    avatar_h = int(avatar_base_img.height * (avatar_w / avatar_base_img.width))
    avatar_resized = avatar_base_img.resize((avatar_w, avatar_h), Image.BICUBIC)

    anim_type = player_cfg.get("avatar_animation", "talking_bob")

    avatar_pos_cfg = player_cfg.get("avatar_position", "bottom_left")
    if avatar_pos_cfg == "bottom_right":
        avatar_xy = (width - avatar_w - 40, height - avatar_h - 180)
    else:  # bottom_left
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

    # 6. Subtitle Overlay Clips
    sub_y = int(height * config.get("captions", {}).get("position_y_ratio", 0.65))

    for chunk in subtitle_chunks:
        c_start = max(0.0, chunk["start"])
        c_end = min(total_duration, chunk["end"] + 0.25)
        c_duration = max(0.1, c_end - c_start)

        # Render subtitle image
        sub_img = render_subtitle_image(chunk["text"], width=width)
        sub_clip = (
            pil_to_image_clip(sub_img, c_duration)
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
        preset="fast",
        threads=4,
        logger=None
    )

    print(f"[Video Composer] Successfully generated video: {output_mp4_path}")
    return output_mp4_path
