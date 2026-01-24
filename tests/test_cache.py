"""Tests for the cache module."""

import os
import tempfile
import pytest
from augent.cache import (
    TranscriptionCache,
    ModelCache,
    CachedTranscription,
)


class TestTranscriptionCache:
    """Tests for TranscriptionCache."""

    @pytest.fixture
    def temp_cache(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TranscriptionCache(cache_dir=tmpdir)
            yield cache

    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary file to simulate an audio file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(b"fake audio content for testing")
            yield f.name
        os.unlink(f.name)

    def test_cache_miss_returns_none(self, temp_cache, sample_audio_file):
        result = temp_cache.get(sample_audio_file, "base")
        assert result is None

    def test_cache_set_and_get(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Hello world",
            "language": "en",
            "duration": 10.5,
            "words": [{"word": "Hello", "start": 0.0, "end": 0.5}],
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}]
        }

        temp_cache.set(sample_audio_file, "base", transcription)
        result = temp_cache.get(sample_audio_file, "base")

        assert result is not None
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.duration == 10.5
        assert len(result.words) == 1
        assert len(result.segments) == 1

    def test_different_models_cached_separately(self, temp_cache, sample_audio_file):
        trans_base = {
            "text": "Base transcription",
            "language": "en",
            "duration": 10.0,
            "words": [],
            "segments": []
        }
        trans_large = {
            "text": "Large transcription",
            "language": "en",
            "duration": 10.0,
            "words": [],
            "segments": []
        }

        temp_cache.set(sample_audio_file, "base", trans_base)
        temp_cache.set(sample_audio_file, "large", trans_large)

        result_base = temp_cache.get(sample_audio_file, "base")
        result_large = temp_cache.get(sample_audio_file, "large")

        assert result_base.text == "Base transcription"
        assert result_large.text == "Large transcription"

    def test_clear_cache(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test",
            "language": "en",
            "duration": 5.0,
            "words": [],
            "segments": []
        }

        temp_cache.set(sample_audio_file, "base", transcription)
        assert temp_cache.get(sample_audio_file, "base") is not None

        count = temp_cache.clear()
        assert count == 1
        assert temp_cache.get(sample_audio_file, "base") is None

    def test_stats(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test",
            "language": "en",
            "duration": 100.0,
            "words": [],
            "segments": []
        }

        # Empty cache
        stats = temp_cache.stats()
        assert stats["entries"] == 0

        # After adding
        temp_cache.set(sample_audio_file, "base", transcription)
        stats = temp_cache.stats()
        assert stats["entries"] == 1
        assert stats["total_audio_duration_hours"] > 0

    def test_hash_audio_file(self, sample_audio_file):
        hash1 = TranscriptionCache.hash_audio_file(sample_audio_file)
        hash2 = TranscriptionCache.hash_audio_file(sample_audio_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestModelCache:
    """Tests for ModelCache (singleton pattern)."""

    def test_singleton_pattern(self):
        cache1 = ModelCache()
        cache2 = ModelCache()
        assert cache1 is cache2

    def test_loaded_models_initially_empty(self):
        cache = ModelCache()
        cache.clear()
        assert cache.loaded_models() == []

    def test_clear(self):
        cache = ModelCache()
        cache.clear()
        assert cache.loaded_models() == []


class TestCachedTranscription:
    """Tests for CachedTranscription dataclass."""

    def test_dataclass_creation(self):
        cached = CachedTranscription(
            audio_hash="abc123",
            model_size="base",
            language="en",
            duration=60.0,
            text="Hello world",
            words=[],
            segments=[],
            created_at=1234567890.0,
            file_path="/path/to/audio.mp3"
        )

        assert cached.audio_hash == "abc123"
        assert cached.model_size == "base"
        assert cached.language == "en"
        assert cached.duration == 60.0
        assert cached.text == "Hello world"
