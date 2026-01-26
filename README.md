<p align="center">
  <img src="./images/logo.png" width="150" alt="Augent Logo">
</p>

<h1 align="center">Augent</h1>

<p align="center">
  <a href="https://github.com/AugentDevs/Augent/actions/workflows/tests.yml"><img src="https://github.com/AugentDevs/Augent/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

<p align="center"><strong>Audio intelligence for Claude Code agents and agentic swarms</strong><br>Built by <a href="https://augent.app">Augent</a></p>

An MCP-powered plugin that gives Claude Code the ability to transcribe, search, and analyze audio files locally. Perfect for agentic automation loops like [Ralph-Wiggum](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) and [Gas Town](https://github.com/steveyegge/gastown).

---

## Watch Nothing. Learn Everything.

Download audio from YouTube tutorials. Augent transcribes them. Claude reads and executes.

**Example: Learning Roblox Game Development**

1. Download audio from 10 Roblox dev tutorials
2. Augent transcribes all of them locally
3. Claude searches for specific techniques ("how to add multiplayer")
4. Claude reads the instructions and runs the commands for you

You skip watching. You skip doing. Claude handles both.

**Why this matters:**

- 10 hours of tutorials → searchable in seconds
- Claude learns from multiple sources at once
- You get the output without the input

This works for any domain: coding tutorials, design workflows, business courses, technical documentation buried in video format.

---

## audio-downloader

A speed-optimized audio downloader built by Augent. Downloads audio ONLY from any video URL at lightning speed.

```bash
audio-downloader "https://youtube.com/watch?v=xxx"
```

**Speed Optimizations:**
- aria2c multi-connection downloads (16 parallel connections)
- Concurrent fragment downloading (4 fragments)
- No video download - audio extraction only
- No format conversion - native audio format for maximum speed

**Supports:** YouTube, Vimeo, SoundCloud, Twitter, TikTok, and 1000+ sites

```bash
# Download to custom folder
audio-downloader -o ~/Music "https://youtube.com/watch?v=xxx"

# Multiple URLs at once
audio-downloader url1 url2 url3

# Show help
audio-downloader --help
```

**Why audio-downloader?**
- Built specifically for the Augent workflow: download → transcribe → search
- Optimized for large files (5+ hour tutorials, full podcasts)
- No unnecessary video data - just the audio you need

---

## Install

```bash
curl -fsSL https://augent.app/install.sh | bash
```

Works on macOS and Linux. Installs everything automatically.

**Windows:** `pip install "augent[all] @ git+https://github.com/AugentDevs/Augent.git"`

### Step 2: Run Web UI

```bash
python3 -m augent.web
```

Open your browser to: **http://127.0.0.1:8888**

### Step 3: Use It

1. **Upload** an audio file (MP3, WAV, M4A, etc.)
2. **Enter keywords** separated by commas (e.g., `lucrative, funding, healthiest`)
3. **Click SEARCH**
4. **View results** with timestamps - click any timestamp to jump to that moment

### Commands Reference

| Command | Description |
|---------|-------------|
| `audio-downloader URL` | Download audio from video URL (speed-optimized) |
| `python3 -m augent.web` | Start Web UI on port 8888 |
| `python3 -m augent.web --port 3000` | Use custom port |
| `python3 -m augent.web --share` | Create public shareable link |
| `augent help` | Show full help manual |
| `augent search audio.mp3 "keyword"` | CLI search |
| `augent transcribe audio.mp3` | Full transcription |
| `augent cache stats` | View cache info |
| `augent cache clear` | Clear cache |

### Troubleshooting

**"command not found: augent"**
```bash
# Use python module directly (always works)
python3 -m augent.web
```

**Port already in use?**
No worries - Augent auto-kills the previous instance and restarts.

**Slow transcription?**
First run downloads the AI model (~75MB for tiny). Subsequent runs are instant due to caching.

---

## Why Augent?

Claude Code agents can now:
- **Search podcasts, interviews, and recordings** for specific keywords with timestamps
- **Find contextual discussions** using proximity search (e.g., "startup" near "funding")
- **Batch process** multiple audio files in parallel
- **Extract audio clips** around keyword matches
- **Cache everything** - no re-transcription needed

Built on [faster-whisper](https://github.com/guillaumekln/faster-whisper) for 2-4x faster transcription than original Whisper.

## Quick Install

```bash
curl -fsSL https://augent.app/install.sh | bash
```

**Windows:** `pip install "augent[all] @ git+https://github.com/AugentDevs/Augent.git"`

## Claude Code Setup

Add to `~/.claude.json` (global) or `.mcp.json` (project):

```json
{
  "mcpServers": {
    "augent": {
      "command": "python3",
      "args": ["-m", "augent.mcp"]
    }
  }
}
```

Then restart Claude Code. Run `/mcp` to verify connection.

**Note:** If `python3` isn't found, use full path (e.g., `/usr/bin/python3` or `/opt/homebrew/bin/python3`).

## MCP Tools

Once configured, Claude has access to:

| Tool | Description |
|------|-------------|
| `download_audio` | Download audio from video URLs at maximum speed (YouTube, Vimeo, TikTok, etc.) |
| `search_audio` | Find keywords with timestamps and context snippets |
| `transcribe_audio` | Full transcription with metadata |
| `search_proximity` | Find where keywords appear near each other |
| `batch_search` | Search multiple files in parallel (for swarms) |
| `list_audio_files` | Discover audio files in a directory |
| `cache_stats` | View transcription cache statistics |
| `clear_cache` | Clear cached transcriptions |

## Agentic Use Cases

### Ralph-Wiggum Style Loops

Perfect for iterative content analysis:

```
Iteration 1: Quick scan with tiny model
Iteration 2: Deep dive on found segments with small model
Iteration 3: Extract clips around key moments
```

### Gas Town Multi-Agent Workflows

Assign audio analysis to worker agents:
- **Agent A**: Transcribe and search podcast library
- **Agent B**: Generate summaries from search results
- **Agent C**: Create clips for social media

### Swarm Patterns

```bash
# Parallel processing across multiple files
augent search "recordings/*.mp3" "AI,automation,future" --workers 4

# Export for downstream agents
augent search audio.mp3 "keyword" --format json --output results.json
```

### Voice Cloning & Style Replication

Train an agent to replicate someone's ad tone or copywriting style using their transcribed audio. Extract speech patterns, phrases, and delivery style from podcasts or recordings.

### Prediction Markets & Research

Extract structured data from earnings calls, interviews, and podcasts for Polymarket research or quantitative analysis.

## CLI Usage

```bash
# Basic search
augent search audio.mp3 "lucrative,funding,healthiest"

# Better accuracy
augent search podcast.mp3 "keyword" --model small

# Batch processing
augent search "podcasts/*.mp3" "keyword" --workers 4

# Export formats
augent search audio.mp3 "keyword" --format csv --output results.csv
augent search audio.mp3 "keyword" --format srt --output matches.srt

# Extract clips around matches
augent search audio.mp3 "keyword" --export-clips ./clips --clip-padding 5

# Proximity search
augent proximity audio.mp3 "startup" "funding" --distance 30

# Full transcription
augent transcribe audio.mp3 --format srt --output subtitles.srt

# Cache management
augent cache stats
augent cache clear
```

## Python API

```python
from augent import search_audio, transcribe_audio, search_audio_proximity

# Basic keyword search
results = search_audio("podcast.mp3", ["lucrative", "funding"])
# {"lucrative": [{"timestamp": "2:34", "snippet": "...a lucrative opportunity..."}]}

# Full transcription
transcription = transcribe_audio("podcast.mp3", model_size="small")

# Proximity search
matches = search_audio_proximity(
    "podcast.mp3",
    keyword1="startup",
    keyword2="funding",
    max_distance=30
)

# Export
from augent import export_matches
csv_output = export_matches(results, format="csv")
```

## Web UI

![Augent Web UI - Upload](./images/webui-1.png)
![Augent Web UI - Results](./images/webui-2.png)

```bash
# Start Web UI
python3 -m augent.web

# Open browser: http://127.0.0.1:8888

# Custom port
python3 -m augent.web --port 3000

# Create public shareable link
python3 -m augent.web --share
```

**Batch processing tip:** Open multiple browser tabs/windows to process files in parallel. Each tab operates independently.

**Note:** The Web UI runs 100% locally - no cloud APIs, no Claude credits used. Transcriptions are cached, so repeat searches on the same file are instant.

## Model Sizes

**`tiny` is the default** - it's the fastest and already incredibly accurate for nearly every use case. You'll use it 99% of the time.

| Model | Speed | Accuracy | VRAM |
|-------|-------|----------|------|
| **tiny** | Fastest | Excellent (default) | ~1GB |
| base | Fast | Excellent | ~1GB |
| small | Medium | Superior | ~2GB |
| medium | Slow | Outstanding | ~5GB |
| large | Slowest | Maximum | ~10GB |

**When to use larger models:**
- Finding lyrics in a song you don't know the name of
- Heavily accented speech or poor audio quality
- Medical/legal transcriptions requiring maximum accuracy
- Non-English languages with complex phonetics

For podcasts, interviews, lectures, and general audio - `tiny` is all you need.

## Caching

Transcriptions are cached to avoid re-processing:

```bash
augent cache stats
# {"entries": 42, "total_audio_duration_hours": 15.5, "cache_size_mb": 12.3}
```

Cache key = file hash + model size, so:
- Same file + same model = instant cache hit
- Same file + different model = new transcription
- Modified file = new transcription

## Requirements

- **Python 3.9+**
- **FFmpeg** (for audio processing)
- **CUDA** (optional, for GPU acceleration)

## Installation Options

```bash
# Basic (CLI only)
pip install -e .

# With Web UI
pip install -e .[web]

# With clip extraction
pip install -e .[clips]

# Everything
pip install -e .[all]

# Development
pip install -e .[dev]
```

## Export Formats

- **JSON** - Structured data, grouped by keyword
- **CSV** - Spreadsheet-ready
- **SRT** - SubRip subtitles
- **VTT** - WebVTT for web video
- **Markdown** - Human-readable reports

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [GitHub Repository](https://github.com/AugentDevs/Augent)
- [Ralph-Wiggum Plugin](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum)
- [Gas Town](https://github.com/steveyegge/gastown)
