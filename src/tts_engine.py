"""High quality neural TTS engine using edge-tts with word-level timestamp extraction."""

import asyncio
import edge_tts
from pathlib import Path
from typing import Dict, Any, List, Tuple
from src.config_loader import load_config

async def generate_speech_and_timestamps_async(
    text: str,
    output_audio_path: str,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "+12%",
    pitch: str = "+0Hz"
) -> List[Dict[str, Any]]:
    """
    Generate MP3 voiceover using edge-tts and collect word-level boundary timestamps.
    Returns list of dicts: [{"word": "word", "start": 0.12, "end": 0.45}, ...]
    """
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    
    words_data: List[Dict[str, Any]] = []

    # Write audio stream and capture SubMaker/events
    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # offset and duration are given in 100-nanosecond units (10,000 units = 1 ms = 0.001 s)
                start_sec = chunk["offset"] / 10_000_000.0
                duration_sec = chunk["duration"] / 10_000_000.0
                end_sec = start_sec + duration_sec
                words_data.append({
                    "word": chunk["text"],
                    "start": round(start_sec, 3),
                    "end": round(end_sec, 3)
                })

    return words_data

def group_words_into_subtitle_chunks(
    words_data: List[Dict[str, Any]],
    words_per_chunk: int = 3
) -> List[Dict[str, Any]]:
    """
    Groups individual word timestamps into short subtitle phrases (2-4 words)
    suited for viral TikTok / Shorts rapid subtitle popups.
    """
    if not words_data:
        return []

    chunks = []
    for i in range(0, len(words_data), words_per_chunk):
        group = words_data[i : i + words_per_chunk]
        chunk_text = " ".join(w["word"] for w in group)
        start_time = group[0]["start"]
        end_time = group[-1]["end"]
        chunks.append({
            "text": chunk_text,
            "start": start_time,
            "end": end_time,
            "words": group
        })
    return chunks

def generate_voiceover(
    script_text: str,
    output_audio_path: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Synchronous wrapper to generate voiceover and subtitle timing chunks.
    """
    config = load_config()
    voice_cfg = config.get("voice", {})
    voice = voice_cfg.get("tts_voice", "en-US-ChristopherNeural")
    rate = voice_cfg.get("tts_rate", "+12%")
    pitch = voice_cfg.get("tts_pitch", "+0Hz")
    words_per_chunk = config.get("captions", {}).get("words_per_subtitle_chunk", 3)

    Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)

    words_data = asyncio.run(
        generate_speech_and_timestamps_async(
            text=script_text,
            output_audio_path=output_audio_path,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
    )

    subtitle_chunks = group_words_into_subtitle_chunks(words_data, words_per_chunk=words_per_chunk)
    return output_audio_path, subtitle_chunks

if __name__ == "__main__":
    test_text = "Did you know that Creepers in Minecraft are completely terrified of tiny cats? Even charged creepers will instantly sprint away!"
    out_file = "test_audio.mp3"
    audio_path, chunks = generate_voiceover(test_text, out_file)
    print(f"Generated audio: {audio_path}")
    print(f"Generated {len(chunks)} subtitle chunks:")
    for c in chunks:
        print(f"  [{c['start']:.2f}s -> {c['end']:.2f}s]: {c['text']}")
