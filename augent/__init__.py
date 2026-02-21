"""
Augent - Local audio keyword search using faster-whisper

Extract timestamped keyword matches from audio files with:
- Transcription memory (skip re-processing)
- Proximity search (find keywords near each other)
- Multiple export formats (JSON, CSV, SRT, VTT, Markdown)
- Audio clip extraction

Usage:
    from augent import search_audio, transcribe_audio

    # Basic keyword search
    results = search_audio("podcast.mp3", ["lucrative", "funding"])

    # Full transcription
    transcription = transcribe_audio("podcast.mp3")

CLI:
    augent search audio.mp3 "keyword1,keyword2"
    augent transcribe audio.mp3 --format srt

Web UI:
    augent-web

MCP Server (for Claude):
    python -m augent.mcp
"""

from .core import (
    search_audio,
    search_audio_full,
    transcribe_audio,
    transcribe_audio_streaming,
    search_audio_proximity,
    search_audio_streaming,
    get_memory_stats,
    clear_memory,
    clear_model_cache,
    list_memories,
    get_memory_by_title,
    TranscriptionProgress,
)

from .search import (
    find_keyword_matches,
    search_with_proximity,
    KeywordSearcher,
)

from .export import (
    export_matches,
    export_transcription,
    Exporter,
)

from .clips import (
    export_clips,
    ClipExtractor,
)

from .memory import (
    get_transcription_memory,
    get_model_cache,
    TranscriptionMemory,
    MemorizedTranscription,
    ModelCache,
)

from .cli import main

# Optional: Speaker diarization (requires simple-diarizer)
try:
    from .speakers import identify_speakers
except ImportError:
    identify_speakers = None

# Optional: Semantic search + chapters (requires sentence-transformers)
try:
    from .embeddings import deep_search, detect_chapters
except ImportError:
    deep_search = None
    detect_chapters = None

# Optional: Text-to-speech (requires kokoro)
try:
    from .tts import text_to_speech, read_aloud
except ImportError:
    text_to_speech = None
    read_aloud = None

__version__ = "2026.2.21"
__all__ = [
    # Core functions
    "search_audio",
    "search_audio_full",
    "transcribe_audio",
    "transcribe_audio_streaming",
    "search_audio_proximity",
    "search_audio_streaming",
    # Memory management
    "get_memory_stats",
    "clear_memory",
    "clear_model_cache",
    "list_memories",
    "get_memory_by_title",
    "get_transcription_memory",
    "get_model_cache",
    # Search
    "find_keyword_matches",
    "search_with_proximity",
    "KeywordSearcher",
    # Export
    "export_matches",
    "export_transcription",
    "export_clips",
    "Exporter",
    "ClipExtractor",
    # Classes
    "TranscriptionProgress",
    "TranscriptionMemory",
    "MemorizedTranscription",
    "ModelCache",
    # Optional: Speakers
    "identify_speakers",
    # Optional: Semantic search + chapters
    "deep_search",
    "detect_chapters",
    # Optional: Text-to-speech
    "text_to_speech",
    "read_aloud",
    # CLI
    "main",
    # Version
    "__version__",
]
