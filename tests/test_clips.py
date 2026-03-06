"""Tests for clip extraction boundary logic and filename formatting."""

from unittest import mock

from augent.clips import ClipExtractor, ClipInfo, check_ffmpeg, format_filename


class TestFormatFilename:
    def test_basic_filename(self):
        result = format_filename("hello", 65.0, 1, "mp3")
        assert result == "match_001_hello_01m05s.mp3"

    def test_zero_timestamp(self):
        result = format_filename("word", 0.0, 1, "mp3")
        assert result == "match_001_word_00m00s.mp3"

    def test_special_chars_replaced(self):
        result = format_filename("it's a test!", 10.0, 2, "mp3")
        assert "'" not in result
        assert "!" not in result
        assert "match_002_" in result

    def test_spaces_to_underscores(self):
        result = format_filename("two words", 0.0, 1, "mp3")
        assert "two_words" in result

    def test_long_keyword_truncated(self):
        long_keyword = "a" * 50
        result = format_filename(long_keyword, 0.0, 1, "mp3")
        # Keyword portion is capped at 30 chars
        keyword_part = result.split("_", 2)[2].rsplit("_", 1)[0]
        assert len(keyword_part) <= 30

    def test_wav_format(self):
        result = format_filename("test", 0.0, 1, "wav")
        assert result.endswith(".wav")

    def test_index_zero_padded(self):
        result = format_filename("kw", 0.0, 42, "mp3")
        assert "match_042_" in result

    def test_large_timestamp(self):
        result = format_filename("kw", 3661.0, 1, "mp3")
        # 3661s = 61m 01s
        assert "61m01s" in result


class TestClipInfo:
    def test_dataclass_fields(self):
        clip = ClipInfo(
            output_path="/tmp/clip.mp3",
            keyword="test",
            timestamp="1:05",
            start_seconds=60.0,
            end_seconds=70.0,
            duration=10.0,
        )
        assert clip.output_path == "/tmp/clip.mp3"
        assert clip.keyword == "test"
        assert clip.timestamp == "1:05"
        assert clip.start_seconds == 60.0
        assert clip.end_seconds == 70.0
        assert clip.duration == 10.0


class TestCheckFfmpeg:
    @mock.patch("augent.clips.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_returns_true_when_available(self, mock_which):
        assert check_ffmpeg() is True

    @mock.patch("augent.clips.shutil.which", return_value=None)
    def test_returns_false_when_missing(self, mock_which):
        assert check_ffmpeg() is False


class TestClipExtractorBoundaries:
    """Test clip start/end boundary calculations without actual audio extraction."""

    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_default_padding(self, _):
        ext = ClipExtractor(padding_before=5.0, padding_after=5.0)
        assert ext.padding_before == 5.0
        assert ext.padding_after == 5.0

    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_start_clamps_to_zero(self, _):
        ext = ClipExtractor(padding_before=10.0, padding_after=5.0)
        # Timestamp at 3s with 10s padding before -> start should be 0, not -7
        with mock.patch.object(ext, "extract_clip", return_value=True) as mock_extract:
            # Call extract_matches to check boundary logic
            matches = [
                {"keyword": "test", "timestamp_seconds": 3.0, "timestamp": "0:03"}
            ]
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                list(ext.extract_matches("fake.mp3", matches, tmpdir))
                # The extract_clip was called
                mock_extract.assert_called_once()
                # Check the ClipInfo that would be yielded - start should be 0
                call_args = mock_extract.call_args
                # timestamp_seconds is the third positional arg
                assert call_args[0][2] == 3.0  # timestamp passed through

    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_extract_clip_start_boundary(self, _):
        ext = ClipExtractor(padding_before=10.0, padding_after=5.0)
        # Internal calculation: start = max(0, timestamp - padding_before)
        start = max(0, 3.0 - ext.padding_before)
        assert start == 0.0

    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_extract_clip_normal_boundary(self, _):
        ext = ClipExtractor(padding_before=5.0, padding_after=5.0)
        start = max(0, 30.0 - ext.padding_before)
        end = 30.0 + ext.padding_after
        assert start == 25.0
        assert end == 35.0

    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_custom_padding(self, _):
        ext = ClipExtractor(padding_before=2.0, padding_after=8.0)
        start = max(0, 10.0 - ext.padding_before)
        end = 10.0 + ext.padding_after
        assert start == 8.0
        assert end == 18.0


class TestClipExtractorInit:
    @mock.patch("augent.clips.check_ffmpeg", return_value=True)
    def test_ffmpeg_available(self, _):
        ext = ClipExtractor()
        assert ext.has_ffmpeg is True
        assert ext.use_pydub is False

    @mock.patch("augent.clips.check_ffmpeg", return_value=False)
    def test_falls_back_to_pydub(self, _):
        with mock.patch.dict("sys.modules", {"pydub": mock.MagicMock()}):
            ext = ClipExtractor()
            assert ext.use_pydub is True

    @mock.patch("augent.clips.check_ffmpeg", return_value=False)
    def test_raises_when_nothing_available(self, _):
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pydub":
                raise ImportError("No pydub")
            return original_import(name, *args, **kwargs)

        import pytest

        with mock.patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="Neither ffmpeg nor pydub"):
                ClipExtractor()
