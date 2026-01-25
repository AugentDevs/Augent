"""
Augent - Local audio keyword search using faster-whisper

Extract timestamped keyword matches from audio files with:
- Transcription caching (skip re-processing)
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
    get_cache_stats,
    clear_cache,
    clear_model_cache,
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

from .cache import (
    get_transcription_cache,
    get_model_cache,
    TranscriptionCache,
    ModelCache,
)

from .cli import main

__version__ = "1.0.0"
__all__ = [
    # Core functions
    "search_audio",
    "search_audio_full",
    "transcribe_audio",
    "transcribe_audio_streaming",
    "search_audio_proximity",
    "search_audio_streaming",
    # Cache management
    "get_cache_stats",
    "clear_cache",
    "clear_model_cache",
    "get_transcription_cache",
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
    "TranscriptionCache",
    "ModelCache",
    # CLI
    "main",
    # Version
    "__version__",
]
