"""Tests for the separator module."""

import os
import tempfile

from augent.separator import SEPARATOR_DIR, _collect_stems, _hash_file


class TestSeparatorUtils:
    """Tests for separator utility functions."""

    def test_hash_file_consistent(self):
        """Same file content produces same hash."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(b"test audio content")
            f.flush()
            path = f.name

        try:
            hash1 = _hash_file(path)
            hash2 = _hash_file(path)
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 hex length
        finally:
            os.unlink(path)

    def test_hash_file_different_content(self):
        """Different file content produces different hashes."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f1:
            f1.write(b"content A")
            f1.flush()
            path1 = f1.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f2:
            f2.write(b"content B")
            f2.flush()
            path2 = f2.name

        try:
            assert _hash_file(path1) != _hash_file(path2)
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_collect_stems_empty_dir(self):
        """Empty directory returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stems = _collect_stems(tmpdir)
            assert stems == {}

    def test_collect_stems_nonexistent_dir(self):
        """Nonexistent directory returns empty dict."""
        stems = _collect_stems("/nonexistent/path")
        assert stems == {}

    def test_collect_stems_finds_wav_files(self):
        """Collects .wav files from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake stem files
            for name in ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]:
                open(os.path.join(tmpdir, name), "w").close()

            stems = _collect_stems(tmpdir)
            assert "vocals" in stems
            assert "drums" in stems
            assert "bass" in stems
            assert "other" in stems
            assert len(stems) == 4

    def test_collect_stems_ignores_non_audio(self):
        """Non-audio files are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "vocals.wav"), "w").close()
            open(os.path.join(tmpdir, "readme.txt"), "w").close()
            open(os.path.join(tmpdir, "config.json"), "w").close()

            stems = _collect_stems(tmpdir)
            assert len(stems) == 1
            assert "vocals" in stems

    def test_separator_dir_is_under_augent(self):
        """Default separator directory is under ~/.augent/."""
        assert ".augent" in SEPARATOR_DIR
        assert "separated" in SEPARATOR_DIR
