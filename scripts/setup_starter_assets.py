"""Helper to generate default ready-to-use starter assets (skin, background music, fonts)."""

import math
import struct
import wave
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
SKINS_DIR = ASSETS_DIR / "skins"
MUSIC_DIR = ASSETS_DIR / "music"
GAMEPLAY_DIR = ASSETS_DIR / "gameplay"

def generate_default_skin():
    SKINS_DIR.mkdir(parents=True, exist_ok=True)
    skin_path = SKINS_DIR / "skin.png"
    if skin_path.exists():
        return

    # Create a 64x64 Minecraft skin template
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Head (8,8 to 15,15)
    draw.rectangle([8, 8, 15, 15], fill=(185, 122, 87, 255))
    # Hair
    draw.rectangle([8, 8, 15, 9], fill=(65, 42, 23, 255))
    # Eyes (White + Cyan/Blue)
    draw.point((9, 11), fill=(255, 255, 255, 255))
    draw.point((10, 11), fill=(44, 98, 180, 255))
    draw.point((13, 11), fill=(44, 98, 180, 255))
    draw.point((14, 11), fill=(255, 255, 255, 255))
    # Nose & Mouth
    draw.point((11, 12), fill=(155, 95, 65, 255))
    draw.point((12, 12), fill=(155, 95, 65, 255))
    draw.rectangle([10, 13, 13, 13], fill=(85, 45, 25, 255))

    # Torso (20,20 to 27,31)
    draw.rectangle([20, 20, 27, 31], fill=(0, 168, 181, 255))
    # Pants (4,20 to 7,31)
    draw.rectangle([4, 20, 7, 31], fill=(43, 52, 128, 255))

    img.save(skin_path)
    print(f"[Starter Assets] Created default player skin at: {skin_path}")

def generate_ambient_music():
    """Generates a pleasant 15-second loopable ambient C418-style music track (WAV)."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    music_path = MUSIC_DIR / "ambient_lofi.wav"
    if music_path.exists():
        return

    sample_rate = 44100
    duration = 16.0  # seconds
    total_samples = int(sample_rate * duration)

    # Chords (Cmaj7, Am7, Fmaj7, G)
    chord_freqs = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [174.61, 220.00, 261.63, 329.63],  # Fmaj7
        [196.00, 246.94, 293.66, 392.00]   # G
    ]

    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        chord_idx = int((t / 4.0)) % len(chord_freqs)
        current_chord = chord_freqs[chord_idx]

        val = 0.0
        # Soft sine waves with gentle attack/decay
        for freq in current_chord:
            # Subtle vibrato
            vibrato = math.sin(2 * math.pi * 4.5 * t) * 1.2
            sine = math.sin(2 * math.pi * (freq + vibrato) * t)
            # Low pass / soft envelope
            val += sine * 0.15

        # Ambient low sub bass
        sub_freq = current_chord[0] / 2
        val += math.sin(2 * math.pi * sub_freq * t) * 0.12

        # Convert to 16-bit integer
        clamped = max(-1.0, min(1.0, val))
        samples.append(int(clamped * 32767 * 0.4))

    # Write WAV file
    with wave.open(str(music_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        packed_data = struct.pack(f"<{len(samples)}h", *samples)
        wav_file.writeframes(packed_data)

    print(f"[Starter Assets] Created ambient background track at: {music_path}")

if __name__ == "__main__":
    generate_default_skin()
    generate_ambient_music()
