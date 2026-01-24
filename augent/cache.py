"""
Augent Cache - Transcription and model caching system

Provides persistent caching for transcriptions to avoid re-processing
the same audio files, and in-memory model caching to avoid reloading.
"""

import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import time


@dataclass
class CachedTranscription:
    """Cached transcription data."""
    audio_hash: str
    model_size: str
    language: str
    duration: float
    text: str
    words: list
    segments: list
    created_at: float
    file_path: str  # Original file path (for reference)


class TranscriptionCache:
    """
    SQLite-based cache for audio transcriptions.

    Stores transcriptions keyed by audio file hash + model size,
    so the same file transcribed with different models is cached separately.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.augent/cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "transcriptions.db"
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    cache_key TEXT PRIMARY KEY,
                    audio_hash TEXT NOT NULL,
                    model_size TEXT NOT NULL,
                    language TEXT,
                    duration REAL,
                    text TEXT,
                    words TEXT,
                    segments TEXT,
                    created_at REAL,
                    file_path TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_hash
                ON transcriptions(audio_hash)
            """)
            conn.commit()

    @staticmethod
    def hash_audio_file(file_path: str) -> str:
        """
        Generate a hash of the audio file content.
        Uses SHA256 for reliable uniqueness.
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks for memory efficiency with large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _cache_key(audio_hash: str, model_size: str) -> str:
        """Generate cache key from audio hash and model size."""
        return f"{audio_hash}:{model_size}"

    def get(self, file_path: str, model_size: str) -> Optional[CachedTranscription]:
        """
        Retrieve cached transcription if available.

        Args:
            file_path: Path to audio file
            model_size: Whisper model size used

        Returns:
            CachedTranscription if found, None otherwise
        """
        try:
            audio_hash = self.hash_audio_file(file_path)
            cache_key = self._cache_key(audio_hash, model_size)

            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM transcriptions WHERE cache_key = ?",
                        (cache_key,)
                    )
                    row = cursor.fetchone()

                    if row is None:
                        return None

                    return CachedTranscription(
                        audio_hash=row['audio_hash'],
                        model_size=row['model_size'],
                        language=row['language'],
                        duration=row['duration'],
                        text=row['text'],
                        words=json.loads(row['words']),
                        segments=json.loads(row['segments']),
                        created_at=row['created_at'],
                        file_path=row['file_path']
                    )
        except Exception:
            # Cache miss on any error
            return None

    def set(self, file_path: str, model_size: str, transcription: Dict[str, Any]) -> None:
        """
        Store transcription in cache.

        Args:
            file_path: Path to audio file
            model_size: Whisper model size used
            transcription: Transcription result dict with text, words, segments, etc.
        """
        try:
            audio_hash = self.hash_audio_file(file_path)
            cache_key = self._cache_key(audio_hash, model_size)

            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO transcriptions
                        (cache_key, audio_hash, model_size, language, duration,
                         text, words, segments, created_at, file_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cache_key,
                        audio_hash,
                        model_size,
                        transcription.get('language', 'unknown'),
                        transcription.get('duration', 0),
                        transcription.get('text', ''),
                        json.dumps(transcription.get('words', [])),
                        json.dumps(transcription.get('segments', [])),
                        time.time(),
                        file_path
                    ))
                    conn.commit()
        except Exception:
            # Silently fail on cache write errors
            pass

    def clear(self) -> int:
        """
        Clear all cached transcriptions.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM transcriptions")
                count = cursor.fetchone()[0]
                conn.execute("DELETE FROM transcriptions")
                conn.commit()
                return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM transcriptions")
            count = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT SUM(duration) FROM transcriptions"
            )
            total_duration = cursor.fetchone()[0] or 0

            # Get DB file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "entries": count,
                "total_audio_duration_hours": round(total_duration / 3600, 2),
                "cache_size_mb": round(db_size / (1024 * 1024), 2),
                "cache_path": str(self.db_path)
            }


class ModelCache:
    """
    In-memory cache for loaded Whisper models.

    Keeps models loaded to avoid expensive reload times
    on consecutive transcriptions.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._model_lock = threading.Lock()
        return cls._instance

    def get(self, model_size: str, device: str = "auto", compute_type: str = "auto"):
        """
        Get a cached model or load a new one.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (auto, cpu, cuda)
            compute_type: Compute type (auto, float16, int8, etc.)

        Returns:
            Loaded WhisperModel instance
        """
        cache_key = f"{model_size}:{device}:{compute_type}"

        with self._model_lock:
            if cache_key not in self._models:
                from faster_whisper import WhisperModel

                # Determine compute type based on device if auto
                if compute_type == "auto":
                    import torch
                    if torch.cuda.is_available():
                        compute_type = "float16"
                    else:
                        compute_type = "int8"

                self._models[cache_key] = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type
                )

            return self._models[cache_key]

    def clear(self):
        """Clear all cached models to free memory."""
        with self._model_lock:
            self._models.clear()

    def loaded_models(self) -> list:
        """List currently loaded model sizes."""
        return list(self._models.keys())


# Global instances for easy access
_transcription_cache: Optional[TranscriptionCache] = None
_model_cache: Optional[ModelCache] = None


def get_transcription_cache(cache_dir: Optional[str] = None) -> TranscriptionCache:
    """Get the global transcription cache instance."""
    global _transcription_cache
    if _transcription_cache is None:
        _transcription_cache = TranscriptionCache(cache_dir)
    return _transcription_cache


def get_model_cache() -> ModelCache:
    """Get the global model cache instance."""
    global _model_cache
    if _model_cache is None:
        _model_cache = ModelCache()
    return _model_cache
