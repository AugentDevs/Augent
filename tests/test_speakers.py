"""Tests for speaker diarization merge logic."""

from augent.speakers import _merge


class TestMergeOverlap:
    """Test that transcription segments are assigned to the correct speaker by overlap."""

    def test_single_speaker_full_overlap(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "Hello world"}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}]
        result = _merge(segments, turns)
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_0"
        assert result[0]["text"] == "Hello world"

    def test_assigns_speaker_with_most_overlap(self):
        segments = [{"start": 4.0, "end": 8.0, "text": "Overlapping segment"}]
        turns = [
            {"speaker": "SPEAKER_0", "start": 0.0, "end": 5.0},
            {"speaker": "SPEAKER_1", "start": 5.0, "end": 10.0},
        ]
        result = _merge(segments, turns)
        assert result[0]["speaker"] == "SPEAKER_1"

    def test_equal_overlap_picks_first(self):
        segments = [{"start": 4.0, "end": 6.0, "text": "Even split"}]
        turns = [
            {"speaker": "SPEAKER_0", "start": 0.0, "end": 5.0},
            {"speaker": "SPEAKER_1", "start": 5.0, "end": 10.0},
        ]
        result = _merge(segments, turns)
        # Both have 1.0s overlap, first match wins (> not >=)
        assert result[0]["speaker"] == "SPEAKER_0"

    def test_multiple_segments_multiple_speakers(self):
        segments = [
            {"start": 0.0, "end": 3.0, "text": "First speaker talking"},
            {"start": 5.0, "end": 8.0, "text": "Second speaker talking"},
            {"start": 10.0, "end": 13.0, "text": "First again"},
        ]
        turns = [
            {"speaker": "Alice", "start": 0.0, "end": 4.0},
            {"speaker": "Bob", "start": 4.0, "end": 9.0},
            {"speaker": "Alice", "start": 9.0, "end": 15.0},
        ]
        result = _merge(segments, turns)
        assert result[0]["speaker"] == "Alice"
        assert result[1]["speaker"] == "Bob"
        assert result[2]["speaker"] == "Alice"

    def test_no_overlap_returns_unknown(self):
        segments = [{"start": 20.0, "end": 25.0, "text": "Gap segment"}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}]
        result = _merge(segments, turns)
        assert result[0]["speaker"] == "Unknown"


class TestMergeOutputFormat:
    """Test that merged output has the expected fields."""

    def test_output_has_required_fields(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "  Hello  "}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}]
        result = _merge(segments, turns)
        assert "speaker" in result[0]
        assert "start" in result[0]
        assert "end" in result[0]
        assert "text" in result[0]
        assert "timestamp" in result[0]

    def test_text_is_stripped(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "  padded text  "}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}]
        result = _merge(segments, turns)
        assert result[0]["text"] == "padded text"

    def test_timestamp_format(self):
        segments = [{"start": 125.0, "end": 130.0, "text": "At two minutes"}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 200.0}]
        result = _merge(segments, turns)
        assert result[0]["timestamp"] == "2:05"

    def test_timestamp_zero(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "Start"}]
        turns = [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}]
        result = _merge(segments, turns)
        assert result[0]["timestamp"] == "0:00"


class TestMergeEdgeCases:
    def test_empty_segments(self):
        result = _merge([], [{"speaker": "SPEAKER_0", "start": 0.0, "end": 10.0}])
        assert result == []

    def test_empty_turns(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "Alone"}]
        result = _merge(segments, [])
        assert len(result) == 1
        assert result[0]["speaker"] == "Unknown"
