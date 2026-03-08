"""
Augent Separator - Audio source separation using Demucs v4

Separates audio into stems (vocals, drums, bass, other) using Meta's
HTDemucs model. The vocal stem feeds directly into transcribe_audio
for clean transcription of noisy recordings.

Requires: pip install augent[separator]
"""

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

# Stem output directory
SEPARATOR_DIR = os.path.join(os.path.expanduser("~"), ".augent", "separated")


def _hash_file(file_path: str) -> str:
    """Generate a hash for an audio file to enable caching."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def separate_audio(
    audio_path: str,
    model: str = "htdemucs",
    two_stems: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Separate an audio file into stems using Demucs v4.

    Args:
        audio_path: Path to the audio file
        model: Demucs model to use. Default: htdemucs (best quality)
        two_stems: If set to "vocals", only separate into vocals + no_vocals.
                   Faster than full 4-stem separation.
        output_dir: Custom output directory. Default: ~/.augent/separated/

    Returns:
        dict with stem file paths, model used, and cached status
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Check demucs is available
    try:
        import demucs  # noqa: F401
    except ImportError:
        raise ImportError(
            "Demucs is not installed. Install it with: pip install augent[separator]\n"
            "Or directly: pip install demucs"
        ) from None

    # Set up output directory
    dest = output_dir or SEPARATOR_DIR
    _ensure_dir(dest)

    # Check cache by file hash
    file_hash = _hash_file(audio_path)
    stem_mode = two_stems or "4stem"
    cache_dir = os.path.join(dest, f"{file_hash}_{model}_{stem_mode}")

    if os.path.exists(cache_dir):
        stems = _collect_stems(cache_dir, two_stems)
        if stems:
            return {
                "stems": stems,
                "model": model,
                "source_file": audio_path,
                "cached": True,
                "output_dir": cache_dir,
            }

    # Run demucs via CLI (most reliable across versions)
    cmd = [
        "python3", "-m", "demucs",
        "--name", model,
        "--out", dest,
        audio_path,
    ]

    if two_stems:
        cmd.extend(["--two-stems", two_stems])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Demucs separation failed:\n{result.stderr}"
        )

    # Demucs outputs to: {out}/{model}/{filename_without_ext}/
    filename_stem = Path(audio_path).stem
    demucs_output = os.path.join(dest, model, filename_stem)

    if not os.path.exists(demucs_output):
        raise RuntimeError(
            f"Demucs output not found at expected path: {demucs_output}\n"
            f"stderr: {result.stderr}"
        )

    # Rename to our cache directory for hash-based lookup
    os.rename(demucs_output, cache_dir)

    # Clean up the model name directory if empty
    model_dir = os.path.join(dest, model)
    if os.path.exists(model_dir) and not os.listdir(model_dir):
        os.rmdir(model_dir)

    stems = _collect_stems(cache_dir, two_stems)

    return {
        "stems": stems,
        "model": model,
        "source_file": audio_path,
        "cached": False,
        "output_dir": cache_dir,
    }


def get_vocal_stem(
    audio_path: str,
    model: str = "htdemucs",
) -> str:
    """
    Extract just the vocal stem from an audio file.

    Optimized for transcription: uses two-stem mode (vocals vs everything else)
    which is faster than full 4-stem separation.

    Args:
        audio_path: Path to the audio file
        model: Demucs model to use

    Returns:
        Path to the vocal stem WAV file
    """
    result = separate_audio(
        audio_path,
        model=model,
        two_stems="vocals",
    )
    vocals_path = result["stems"].get("vocals")
    if not vocals_path:
        raise RuntimeError("Vocal stem not found in separation output")
    return vocals_path


def _collect_stems(output_dir: str, two_stems: Optional[str] = None) -> Dict[str, str]:
    """Collect stem file paths from a demucs output directory."""
    stems = {}
    if not os.path.exists(output_dir):
        return stems

    for f in os.listdir(output_dir):
        if f.endswith(".wav") or f.endswith(".mp3") or f.endswith(".flac"):
            stem_name = Path(f).stem
            stems[stem_name] = os.path.join(output_dir, f)

    return stems
