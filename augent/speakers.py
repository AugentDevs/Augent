"""
Augent Speakers - Speaker diarization

Uses pyannote-audio for state-of-the-art speaker diarization.
Automatically detects who speaks when and how many speakers are present.

Models are bundled with Augent (downloaded during install). No API keys
or tokens required.

Requires: pip install augent[speakers]
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import transcribe_audio
from .memory import get_transcription_memory

# Where the installer places pre-downloaded pyannote models
_MODELS_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")


def identify_speakers(
    audio_path: str,
    model_size: str = "tiny",
    num_speakers: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Identify speakers in audio and return speaker-labeled transcript.

    Runs faster-whisper transcription (from memory) then pyannote diarization,
    merging results by timestamp overlap.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Step 1: Get transcription (from memory)
    transcription = transcribe_audio(audio_path, model_size)

    # Step 2: Check diarization memory
    memory = get_transcription_memory()
    audio_hash = memory.hash_audio_file(audio_path)
    stored_diarization = memory.get_diarization(audio_hash, num_speakers)

    if stored_diarization:
        turns = stored_diarization["turns"]
        speakers = stored_diarization["speakers"]
    else:
        # Step 3: Run diarization with pyannote
        try:
            from pyannote.audio import Pipeline
        except ImportError:
            raise ImportError(
                "pyannote-audio is not installed. Install with: pip install augent[speakers]\n"
                "Or directly: pip install pyannote-audio"
            ) from None

        # Models are pre-downloaded by the installer to the HuggingFace cache.
        # Load from local cache (no token needed).
        model_dir = os.path.join(
            _MODELS_CACHE, "models--pyannote--speaker-diarization-3.1"
        )
        if not os.path.exists(model_dir):
            raise RuntimeError(
                "Pyannote speaker diarization models not found.\n"
                "Run the Augent installer to download them:\n"
                "  curl -fsSL https://augent.app/install.sh | bash\n"
                "Or reinstall with: pip install augent[speakers]"
            )

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
        )

        # Run diarization
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers

        diarization = pipeline(audio_path, **kwargs)

        # Extract turns from pyannote Annotation
        turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append(
                {
                    "speaker": speaker,
                    "start": float(turn.start),
                    "end": float(turn.end),
                }
            )

        speakers = sorted({t["speaker"] for t in turns})

        # Store the result
        memory.set_diarization(audio_hash, speakers, turns, num_speakers)

    # Step 4: Merge transcription segments with speaker turns
    merged = _merge(transcription["segments"], turns)

    return {
        "speakers": speakers,
        "segments": merged,
        "duration": transcription["duration"],
        "duration_formatted": f"{int(transcription['duration'] // 60)}:{int(transcription['duration'] % 60):02d}",
        "language": transcription["language"],
        "cached": transcription.get("cached", False),
    }


def _merge(transcript_segments: List[Dict], speaker_turns: List[Dict]) -> List[Dict]:
    """Merge transcription segments with speaker turns by timestamp overlap."""
    merged = []
    for seg in transcript_segments:
        seg_start = seg["start"]
        seg_end = seg["end"]

        # Find speaker with maximum overlap
        best_speaker = "Unknown"
        best_overlap = 0.0

        for turn in speaker_turns:
            overlap_start = max(seg_start, turn["start"])
            overlap_end = min(seg_end, turn["end"])
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        merged.append(
            {
                "speaker": best_speaker,
                "start": seg_start,
                "end": seg_end,
                "text": seg["text"].strip(),
                "timestamp": f"{int(seg_start // 60)}:{int(seg_start % 60):02d}",
            }
        )

    return merged
