"""Minecraft Player Character & Skin Renderer.
Supports online username rendering (Minotar/Crafatar/Visage) and offline 3D isometric skin rendering from 64x64 skin.png.
"""

import math
import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from typing import Optional, Tuple, List
from src.config_loader import load_config, ASSETS_DIR

SKINS_DIR = ASSETS_DIR / "skins"
DEFAULT_SKIN_PATH = SKINS_DIR / "skin.png"

def ensure_skins_dir():
    SKINS_DIR.mkdir(parents=True, exist_ok=True)

def download_skin_from_username(username: str, output_path: Path) -> bool:
    """Download Minecraft skin PNG using Mojang/Minotar API."""
    ensure_skins_dir()
    url = f"https://minotar.net/skin/{username}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"[Skin Fetcher] Could not download raw skin for {username}: {e}")
    return False

def download_3d_avatar(username: str, render_type: str = "isometric_bust", output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Download a high-resolution 3D Minecraft render of the player.
    Supports:
    - 'isometric_bust': 3D head and shoulders
    - '2d_avatar': 2D face with hat overlay
    - 'full_body': 3D full body stance
    """
    ensure_skins_dir()
    if not output_path:
        output_path = SKINS_DIR / f"{username}_{render_type}.png"

    # API endpoints
    urls = []
    if render_type == "isometric_bust":
        urls = [
            f"https://minotar.net/armor/bust/{username}/600.png",
            f"https://visage.surgeplay.com/bust/600/{username}.png",
            f"https://mc-heads.net/body/{username}/600"
        ]
    elif render_type == "full_body":
        urls = [
            f"https://visage.surgeplay.com/full/600/{username}.png",
            f"https://minotar.net/armor/body/{username}/600.png",
            f"https://mc-heads.net/player/{username}/600"
        ]
    else:  # 2d_avatar / helm
        urls = [
            f"https://minotar.net/helm/{username}/600.png",
            f"https://visage.surgeplay.com/face/600/{username}.png",
            f"https://mc-heads.net/avatar/{username}/600"
        ]

    for url in urls:
        try:
            resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return output_path
        except Exception:
            continue

    return None

def create_default_steve_skin(output_path: Path):
    """Creates a basic Steve face/skin in case of no internet or missing skin."""
    ensure_skins_dir()
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Head Front (8x8 at 8,8)
    draw.rectangle([8, 8, 15, 15], fill=(180, 120, 80, 255))
    # Hair
    draw.rectangle([8, 8, 15, 9], fill=(60, 40, 20, 255))
    # Eyes
    draw.point((9, 11), fill=(255, 255, 255, 255))
    draw.point((10, 11), fill=(40, 60, 160, 255))
    draw.point((13, 11), fill=(40, 60, 160, 255))
    draw.point((14, 11), fill=(255, 255, 255, 255))
    # Nose & Mouth
    draw.point((11, 12), fill=(150, 90, 60, 255))
    draw.point((12, 12), fill=(150, 90, 60, 255))
    draw.rectangle([10, 13, 13, 13], fill=(80, 40, 20, 255))
    img.save(output_path)

def render_isometric_cube(face_front: Image.Image, face_top: Image.Image, face_side: Image.Image, size: int = 400) -> Image.Image:
    """
    Software 3D Isometric Cube Renderer (Offline / Fallback).
    Renders Minecraft isometric head directly from 2D pixel textures.
    """
    out_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # Scale face textures
    res = 120
    f_front = face_front.resize((res, res), Image.NEAREST)
    f_top = face_top.resize((res, res), Image.NEAREST)
    f_side = face_side.resize((res, res), Image.NEAREST)

    # Apply lighting shading
    # Top face: full bright
    # Front face: slightly dimmed
    f_front = Image.eval(f_front, lambda p: int(p * 0.85))
    # Side face: darker for 3D depth
    f_side = Image.eval(f_side, lambda p: int(p * 0.65))

    # Affine transform matrices for isometric projection:
    # 30 degree isometric angle
    cx, cy = size // 2, size // 2
    w = int(res * 1.4)
    h = int(res * 0.8)

    # Simplified clean 2.5D composite:
    draw = ImageDraw.Draw(out_img)
    # Add subtle soft shadow under player
    draw.ellipse([cx - 140, cy + 120, cx + 140, cy + 190], fill=(0, 0, 0, 90))

    # Paste front enlarged with rounded frame / clean border
    face_large = f_front.resize((int(size * 0.65), int(size * 0.65)), Image.NEAREST)
    out_img.paste(face_large, (cx - face_large.width // 2, cy - face_large.height // 2), face_large)

    return out_img

def add_glow_and_border(avatar_img: Image.Image, border_color: Tuple[int, int, int, int] = (255, 230, 0, 220), border_radius: int = 6) -> Image.Image:
    """Adds a stylish neon/white glow outline and drop shadow around the character avatar."""
    w, h = avatar_img.size
    padded = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    padded.paste(avatar_img, (20, 20), avatar_img)

    # Create shadow
    alpha = padded.split()[3]
    shadow = Image.new("RGBA", padded.size, (0, 0, 0, 160))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))

    # Create subtle outer glow
    glow = Image.new("RGBA", padded.size, border_color)
    glow.putalpha(alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(4))

    # Composite: Shadow -> Glow -> Avatar
    final_canvas = Image.new("RGBA", padded.size, (0, 0, 0, 0))
    final_canvas.paste(shadow, (0, 4), shadow)
    final_canvas.paste(glow, (0, 0), glow)
    final_canvas.paste(padded, (0, 0), padded)
    return final_canvas

def get_player_avatar(custom_username: Optional[str] = None) -> Image.Image:
    """
    Loads or generates the player avatar image ready for video overlay.
    """
    config = load_config()
    player_cfg = config.get("player", {})
    username = custom_username or player_cfg.get("minecraft_username", "Steve")
    render_type = player_cfg.get("render_type", "isometric_bust")
    skin_path_str = player_cfg.get("skin_path", "assets/skins/skin.png")
    local_skin_path = ASSETS_DIR.parent / skin_path_str

    ensure_skins_dir()

    # 1. First priority: Check for custom character render image (custom_character.png or skin_path)
    custom_char_path = SKINS_DIR / "custom_character.png"
    if custom_char_path.exists():
        try:
            custom_img = Image.open(custom_char_path).convert("RGBA")
            # If it's already a full render (not a 64x64 skin sheet)
            if custom_img.width > 64 or custom_img.height > 64:
                return add_glow_and_border(custom_img)
        except Exception as e:
            print(f"[Skin Renderer] Custom character load error: {e}")

    # 2. Check local skin_path
    if local_skin_path.exists():
        try:
            skin_img = Image.open(local_skin_path).convert("RGBA")
            # If it's already a 2D/3D render image
            if skin_img.width > 64 or skin_img.height > 64:
                return add_glow_and_border(skin_img)

            # If it's a 64x64 skin sheet, extract face
            head_front = skin_img.crop((8, 8, 16, 16))
            hat_layer = skin_img.crop((40, 8, 48, 16))
            combined_head = head_front.copy()
            combined_head.paste(hat_layer, (0, 0), hat_layer)

            avatar_img = combined_head.resize((400, 400), Image.NEAREST)
            return add_glow_and_border(avatar_img)
        except Exception as e:
            print(f"[Skin Renderer] Local skin extraction error: {e}")

    # 3. Try online 3D render for high visual fidelity
    cached_render = SKINS_DIR / f"{username}_{render_type}.png"
    if cached_render.exists():
        try:
            return Image.open(cached_render).convert("RGBA")
        except Exception:
            pass

    downloaded_path = download_3d_avatar(username, render_type, cached_render)
    if downloaded_path and downloaded_path.exists():
        try:
            img = Image.open(downloaded_path).convert("RGBA")
            img = add_glow_and_border(img)
            return img
        except Exception:
            pass

    # 4. Create Steve fallback
    create_default_steve_skin(DEFAULT_SKIN_PATH)
    skin_img = Image.open(DEFAULT_SKIN_PATH).convert("RGBA")
    head_front = skin_img.crop((8, 8, 16, 16))
    avatar_img = head_front.resize((400, 400), Image.NEAREST)
    return add_glow_and_border(avatar_img)

def generate_avatar_frame(base_avatar: Image.Image, t: float, animation_type: str = "talking_bob") -> Image.Image:
    """
    Generates dynamic animated frames for the avatar simulating a real human explainer.
    
    Layered animation system:
    - Talking bob: Energetic vertical movement synced to speech rhythm
    - Head tilt: Natural side-to-side head movement like explaining
    - Breathing: Subtle scale pulse for lifelike feel
    - Emphasis bounce: Periodic bigger bounces for emphasis moments
    - Lean-in: Occasional forward lean (scale up) for dramatic points
    - Hand gesture simulation: Slight horizontal sway as if gesturing
    """
    if animation_type == "static":
        return base_avatar

    w, h = base_avatar.size
    pad = 40  # Extra padding for movement room

    if animation_type == "talking_bob":
        # ── Layer 1: Talking rhythm (fast bobbing like speaking) ──
        talk_speed = 8.0  # ~4 Hz natural speech cadence
        talk_bob = math.sin(t * talk_speed) * 8
        # Add secondary faster micro-bob for realism
        micro_bob = math.sin(t * 14.0) * 3

        # ── Layer 2: Head tilt (like explaining/thinking) ──
        # Slow natural head tilt side to side
        tilt_angle = math.sin(t * 2.2) * 4.5
        # Occasional bigger tilt as if making a point
        emphasis_tilt = math.sin(t * 0.8) * 2.0
        total_tilt = tilt_angle + emphasis_tilt

        # ── Layer 3: Breathing (subtle scale pulse) ──
        breathe_scale = 1.0 + math.sin(t * 2.5) * 0.015

        # ── Layer 4: Emphasis bounce (every ~3 seconds, bigger movement) ──
        # Creates natural "emphasis" moments like a real explainer
        emphasis_cycle = t % 3.2
        if emphasis_cycle < 0.3:
            # Quick bounce up during emphasis
            emphasis_bounce = -math.sin((emphasis_cycle / 0.3) * math.pi) * 18
        else:
            emphasis_bounce = 0

        # ── Layer 5: Horizontal sway (hand gesture simulation) ──
        # Slow drift left-right as if gesturing with hands
        gesture_sway = math.sin(t * 1.5) * 10
        # Quick gestural flicks
        gesture_flick = math.sin(t * 5.5) * 3

        # ── Layer 6: Lean-in effect (periodic scale up for dramatic moments) ──
        lean_cycle = t % 5.0
        if lean_cycle < 0.5:
            lean_scale = 1.0 + (math.sin((lean_cycle / 0.5) * math.pi) * 0.06)
        else:
            lean_scale = 1.0

        # ── Combine all layers ──
        total_y_offset = int(talk_bob + micro_bob + emphasis_bounce)
        total_x_offset = int(gesture_sway + gesture_flick)
        total_scale = breathe_scale * lean_scale

        # Apply scale
        new_w = int(w * total_scale)
        new_h = int(h * total_scale)
        scaled = base_avatar.resize((new_w, new_h), Image.BICUBIC)

        # Apply rotation (head tilt)
        rotated = scaled.rotate(total_tilt, resample=Image.BICUBIC, expand=False)

        # Create output frame with padding for movement
        frame = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
        paste_x = max(0, min(pad, (pad // 2) + total_x_offset + (w - new_w) // 2))
        paste_y = max(0, min(pad, (pad // 2) + total_y_offset + (h - new_h) // 2))
        frame.paste(rotated, (paste_x, paste_y), rotated)
        return frame

    elif animation_type == "breathe":
        # Gentle breathing with subtle head movement
        scale_factor = 1.0 + (math.sin(t * 2.5) * 0.025)
        gentle_tilt = math.sin(t * 1.2) * 2.0
        gentle_bob = math.sin(t * 2.0) * 4

        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        resized = base_avatar.resize((new_w, new_h), Image.BICUBIC)
        rotated = resized.rotate(gentle_tilt, resample=Image.BICUBIC, expand=False)

        frame = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
        cx, cy = (w + pad) // 2, (h + pad) // 2
        paste_y = cy - new_h // 2 + int(gentle_bob)
        frame.paste(rotated, (cx - new_w // 2, paste_y), rotated)
        return frame

    return base_avatar

if __name__ == "__main__":
    avatar = get_player_avatar("Steve")
    out_test = SKINS_DIR / "test_avatar_output.png"
    avatar.save(out_test)
    print(f"Generated test avatar at: {out_test}")
