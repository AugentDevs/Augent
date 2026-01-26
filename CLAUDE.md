# Augent - Claude Code Plugin

Augent is an MCP-powered audio intelligence plugin for Claude Code. It enables AI agents to transcribe, search, and analyze audio files locally using faster-whisper.

## audio-downloader (Built by Augent)

A speed-optimized audio downloader for downloading audio ONLY from any video URL at lightning speed.

```bash
# Download audio from YouTube (or any video URL)
audio-downloader "https://youtube.com/watch?v=xxx"

# Download to custom folder
audio-downloader -o ~/Music "https://youtube.com/watch?v=xxx"

# Download multiple URLs
audio-downloader url1 url2 url3
```

**Speed Optimizations:**
- aria2c multi-connection downloads (16 parallel connections)
- Concurrent fragment downloading (4 fragments)
- No video download - audio extraction only
- No format conversion - native audio format

**Supports:** YouTube, Vimeo, SoundCloud, Twitter, TikTok, and 1000+ sites

**Workflow:** Download → Transcribe → Search
```bash
audio-downloader "https://youtube.com/watch?v=tutorial"
augent transcribe ~/Downloads/tutorial.webm
augent search ~/Downloads/tutorial.webm "keyword1,keyword2"
```

## Quick Start (For Claude)

You have access to these tools via the MCP server:

### download_audio
Download audio from video URLs at maximum speed. Uses aria2c multi-connection downloads and concurrent fragments. Downloads audio ONLY - never video.
```
url: "https://youtube.com/watch?v=xxx"
output_dir: "~/Downloads" (optional, default)
```
Returns the downloaded file path, ready for transcription.

### search_audio
Search for keywords in audio files with timestamped results.
```
audio_path: "/path/to/audio.mp3"
keywords: ["lucrative", "funding", "healthiest"]
model_size: "tiny" (optional, default)
include_full_text: false (optional)
```

### transcribe_audio
Get full transcription of an audio file.
```
audio_path: "/path/to/audio.mp3"
model_size: "tiny" (optional)
```

### search_proximity
Find where two keywords appear near each other.
```
audio_path: "/path/to/audio.mp3"
keyword1: "startup"
keyword2: "funding"
max_distance: 30 (optional, words between)
```

### batch_search
Search multiple audio files in parallel - ideal for swarms.
```
audio_paths: ["/path/to/file1.mp3", "/path/to/file2.mp3"]
keywords: ["keyword1", "keyword2"]
model_size: "tiny" (optional)
workers: 2 (optional, parallel workers)
```

### list_audio_files
Discover audio files in a directory before batch processing.
```
directory: "/path/to/audio/folder"
pattern: "*.mp3" (optional, glob pattern)
recursive: false (optional, search subdirectories)
```

### cache_stats
View cache statistics - no parameters needed.

### clear_cache
Clear transcription cache - no parameters needed.

## Model Sizes

**`tiny` is the default** - it's the fastest and already incredibly accurate. Use it for nearly everything.

| Model  | Speed    | Accuracy   |
|--------|----------|------------|
| **tiny** | Fastest | Excellent (default) |
| base   | Fast     | Excellent  |
| small  | Medium   | Superior   |
| medium | Slow     | Outstanding |
| large  | Slowest  | Maximum    |

**When to use larger models:**
- Finding lyrics in a song you don't know the name of
- Heavily accented speech or poor audio quality
- Medical/legal transcriptions requiring maximum accuracy

**Warning:** `medium` and `large` models are very CPU/memory intensive. They can freeze or overheat lower-spec machines. Stick to `tiny` or `base` unless the user has a powerful machine.

For tutorials, interviews, lectures - `tiny` handles it.

## Caching Behavior

- Transcriptions are cached by file hash + model size
- Same file, same model = instant cache hit
- Same file, different model = new transcription
- Modified file = new transcription
- Cache persists at `~/.augent/cache/transcriptions.db`

## CLI Commands (via Bash)

```bash
# Download audio from video URL (speed-optimized)
audio-downloader "https://youtube.com/watch?v=xxx"
audio-downloader -o ~/Music "https://youtube.com/watch?v=xxx"

# Search audio
augent search audio.mp3 "keyword1,keyword2"

# Batch processing
augent search "*.mp3" "keyword" --workers 4

# Full transcription
augent transcribe audio.mp3 --format srt

# Proximity search
augent proximity audio.mp3 "startup" "funding" --distance 30

# Export formats: json, csv, srt, vtt, markdown
augent search audio.mp3 "keyword" --format csv --output results.csv

# Cache management
augent cache stats
augent cache clear
```

## Best Practices for Agentic Workflows

1. **Start with `tiny` model** - Fast iteration, upgrade to `small` for final pass
2. **Use caching** - Transcriptions persist, enabling rapid re-search
3. **Batch processing** - Use glob patterns for multiple files
4. **Proximity search** - Find contextual discussions (e.g., "problem" near "solution")
5. **Export results** - CSV/JSON for structured data, SRT/VTT for video integration

## Example Agentic Patterns

### Content Discovery Loop
```python
# 1. Quick scan with tiny model
results = search_audio("podcast.mp3", ["AI", "automation"], model_size="tiny")

# 2. If matches found, re-analyze with better model
if results:
    detailed = search_audio("podcast.mp3", ["AI", "automation"], model_size="small")
```

### Multi-File Analysis
```bash
# Process all audio files in directory
augent search "recordings/*.mp3" "keyword" --workers 4 --format json --output results.json
```

### Clip Extraction
```bash
# Extract audio segments around keyword matches
augent search audio.mp3 "important moment" --export-clips ./clips --clip-padding 5
```

## Web UI Batch Processing

The Web UI at `http://localhost:9797` runs 100% locally (no Claude credits used).

For parallel processing: open multiple browser tabs to the same URL. Each tab processes independently, enabling manual batch workflows.

## Requirements

- Python 3.9+
- FFmpeg (for audio processing)
- yt-dlp + aria2 (for audio-downloader)
- CUDA (optional, for GPU acceleration)
