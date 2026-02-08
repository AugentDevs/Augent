"""
Augent TTS - Text-to-speech using Kokoro

Converts text to natural speech audio using the Kokoro 82M model.
No account, no API key — fully local, Apache 2.0 licensed.

System dependency: espeak-ng (brew install espeak-ng on macOS)
"""

import os
import shutil
from datetime import datetime
from typing import Any, Dict, Optional

SAMPLE_RATE = 24000

LANG_MAP = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "j": "Japanese",
    "p": "Brazilian Portuguese",
    "z": "Mandarin Chinese",
}


def text_to_speech(
    text: str,
    voice: str = "af_heart",
    output_dir: str = "~/Desktop",
    output_filename: Optional[str] = None,
    speed: float = 1.0,
) -> Dict[str, Any]:
    """
    Convert text to speech audio using Kokoro TTS.

    Args:
        text: Text to convert to speech.
        voice: Voice ID (e.g. af_heart, am_adam, bf_emma). Default: af_heart.
        output_dir: Directory to save the audio file. Default: ~/Desktop.
        output_filename: Custom filename. Auto-generated if not set.
        speed: Speech speed multiplier. Default: 1.0.

    Returns:
        Dict with file_path, voice, language, duration, sample_rate, text_length.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Check espeak-ng is installed
    if not shutil.which("espeak-ng"):
        raise RuntimeError(
            "espeak-ng not found. Install with: brew install espeak-ng (macOS) "
            "or apt-get install espeak-ng (Linux)"
        )

    # Lazy imports
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    # Detect language from voice prefix
    lang_code = voice[0] if voice else "a"
    language = LANG_MAP.get(lang_code, "American English")

    # Create pipeline
    pipeline = KPipeline(lang_code=lang_code)

    # Generate audio
    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed):
        if audio is not None:
            chunks.append(audio)

    if not chunks:
        raise RuntimeError("No audio generated. Check that the text and voice are valid.")

    # Concatenate all chunks
    full_audio = np.concatenate(chunks)

    # Prepare output path
    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tts_{timestamp}.wav"

    if not output_filename.endswith(".wav"):
        output_filename += ".wav"

    file_path = os.path.join(output_dir, output_filename)

    # Save
    sf.write(file_path, full_audio, SAMPLE_RATE)

    duration = len(full_audio) / SAMPLE_RATE

    return {
        "file_path": file_path,
        "voice": voice,
        "language": language,
        "duration": round(duration, 2),
        "duration_formatted": f"{int(duration // 60)}:{int(duration % 60):02d}",
        "sample_rate": SAMPLE_RATE,
        "text_length": len(text),
    }
