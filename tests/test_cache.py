"""Tests for the cache module."""

import os
import sqlite3
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
        assert "titles" in stats
        assert len(stats["titles"]) == 1
        assert "md_dir" in stats

    def test_hash_audio_file(self, sample_audio_file):
        hash1 = TranscriptionCache.hash_audio_file(sample_audio_file)
        hash2 = TranscriptionCache.hash_audio_file(sample_audio_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    # --- Title and markdown tests ---

    def test_set_populates_title(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test", "language": "en", "duration": 5.0,
            "words": [], "segments": []
        }
        temp_cache.set(sample_audio_file, "base", transcription)
        result = temp_cache.get(sample_audio_file, "base")
        assert result is not None
        assert result.title != ""

    def test_set_creates_markdown_file(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Hello world this is a test",
            "language": "en",
            "duration": 10.5,
            "words": [{"word": "Hello", "start": 0.0, "end": 0.5}],
            "segments": [{"start": 0.0, "end": 5.0, "text": "Hello world this is a test"}]
        }
        temp_cache.set(sample_audio_file, "base", transcription)

        md_files = list(temp_cache.md_dir.glob("*.md"))
        assert len(md_files) == 1

        content = md_files[0].read_text()
        assert "Hello world" in content
        assert "[0:00]" in content

    def test_markdown_contains_metadata(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test content",
            "language": "en",
            "duration": 125.0,
            "words": [],
            "segments": [{"start": 0.0, "end": 5.0, "text": "Test content"}]
        }
        temp_cache.set(sample_audio_file, "base", transcription)

        md_files = list(temp_cache.md_dir.glob("*.md"))
        content = md_files[0].read_text()
        assert "**Duration:** 2:05" in content
        assert "**Language:** en" in content

    def test_get_by_title(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test", "language": "en", "duration": 5.0,
            "words": [], "segments": []
        }
        temp_cache.set(sample_audio_file, "base", transcription)

        # The title is derived from the temp file name
        title = TranscriptionCache._title_from_path(sample_audio_file)
        results = temp_cache.get_by_title(title[:5])
        assert len(results) >= 1
        assert results[0].text == "Test"

    def test_get_by_title_no_match(self, temp_cache):
        results = temp_cache.get_by_title("nonexistent_title_xyz")
        assert len(results) == 0

    def test_list_all_empty(self, temp_cache):
        entries = temp_cache.list_all()
        assert entries == []

    def test_list_all_with_entries(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test", "language": "en", "duration": 120.0,
            "words": [], "segments": []
        }
        temp_cache.set(sample_audio_file, "base", transcription)

        entries = temp_cache.list_all()
        assert len(entries) == 1
        assert "title" in entries[0]
        assert entries[0]["duration_formatted"] == "2:00"
        assert "md_path" in entries[0]
        assert "date" in entries[0]

    def test_clear_removes_markdown_files(self, temp_cache, sample_audio_file):
        transcription = {
            "text": "Test", "language": "en", "duration": 5.0,
            "words": [], "segments": [{"start": 0.0, "end": 5.0, "text": "Test"}]
        }
        temp_cache.set(sample_audio_file, "base", transcription)

        md_files = list(temp_cache.md_dir.glob("*.md"))
        assert len(md_files) == 1

        temp_cache.clear()

        md_files = list(temp_cache.md_dir.glob("*.md"))
        assert len(md_files) == 0

    def test_db_migration_adds_columns(self):
        """Test that opening a DB without title/md_path columns adds them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "transcriptions.db")

            # Create a DB with the old schema (no title, no md_path)
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE transcriptions (
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
                    INSERT INTO transcriptions VALUES
                    ('hash1:tiny', 'hash1', 'tiny', 'en', 60.0,
                     'old text', '[]', '[]', 1000000.0, '/old/path.mp3')
                """)
                conn.commit()

            # Now open with TranscriptionCache which triggers migration
            cache = TranscriptionCache(cache_dir=tmpdir)

            # Verify old data still accessible
            stats = cache.stats()
            assert stats["entries"] == 1

            # Verify new columns exist (list_all uses them)
            entries = cache.list_all()
            assert len(entries) == 1
            # Old row has empty title in DB, list_all falls back to basename
            assert entries[0]["title"] == "path.mp3"


class TestTitleDerivation:
    """Tests for title extraction and sanitization."""

    def test_title_from_simple_path(self):
        title = TranscriptionCache._title_from_path("/path/to/My Podcast Episode.mp3")
        assert title == "My Podcast Episode"

    def test_title_from_path_strips_extension(self):
        title = TranscriptionCache._title_from_path("/downloads/audio.webm")
        assert title == "audio"

    def test_title_preserves_spaces(self):
        title = TranscriptionCache._title_from_path("/path/How to Build a Startup.mp3")
        assert title == "How to Build a Startup"

    def test_sanitize_filename_removes_special_chars(self):
        sanitized = TranscriptionCache._sanitize_filename("Hello: World! (2024) [HD]")
        assert ":" not in sanitized
        assert "!" not in sanitized
        assert "[" not in sanitized
        assert len(sanitized) > 0

    def test_sanitize_filename_truncates_long_titles(self):
        long_title = "A" * 300
        sanitized = TranscriptionCache._sanitize_filename(long_title)
        assert len(sanitized) <= 200

    def test_sanitize_filename_handles_empty(self):
        sanitized = TranscriptionCache._sanitize_filename("")
        assert sanitized == "untitled"

    def test_sanitize_filename_collapses_underscores(self):
        sanitized = TranscriptionCache._sanitize_filename("hello___world   test")
        assert "__" not in sanitized
        assert "  " not in sanitized


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
        assert cached.title == ""  # Default

    def test_dataclass_with_title(self):
        cached = CachedTranscription(
            audio_hash="abc123",
            model_size="base",
            language="en",
            duration=60.0,
            text="Hello world",
            words=[],
            segments=[],
            created_at=1234567890.0,
            file_path="/path/to/audio.mp3",
            title="My Podcast"
        )

        assert cached.title == "My Podcast"
