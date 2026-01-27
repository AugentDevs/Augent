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

## Install

```bash
curl -fsSL https://augent.app/install.sh | bash
```

Works on macOS and Linux. Installs everything automatically.

**Windows:** `pip install "augent[all] @ git+https://github.com/AugentDevs/Augent.git"`

---

## Usage

Augent can be used in three ways:

| Mode | Best For |
|------|----------|
| **Claude Code (MCP)** | Automated agentic workflows - Claude transcribes and searches for you |
| **CLI** | Quick terminal-based searches and batch processing |
| **Web UI** | Visual interface for manual uploads and searches |

---

## Claude Code (MCP)

The primary way to use Augent. Claude Code gets direct access to audio intelligence tools.

### Setup

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

Restart Claude Code. Run `/mcp` to verify connection.

**Note:** If `python3` isn't found, use full path (e.g., `/usr/bin/python3` or `/opt/homebrew/bin/python3`).

### MCP Tools

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

### Example Workflow

Ask Claude: *"Download this YouTube tutorial and find where they talk about multiplayer"*

Claude will:
1. `download_audio` → Downloads audio from the URL
2. `search_audio` → Finds "multiplayer" mentions with timestamps
3. Returns results with exact timestamps and context

---

## CLI

For terminal-based usage. Works standalone or inside Claude Code.

![Augent CLI](./images/cli-help.png)

### Commands

| Command | Description |
|---------|-------------|
| `audio-downloader URL` | Download audio from video URL to ~/Downloads |
| `augent search audio.mp3 "keyword"` | Search for keywords |
| `augent transcribe audio.mp3` | Full transcription |
| `augent proximity audio.mp3 "A" "B"` | Find keyword A near keyword B |
| `augent cache stats` | View cache info |
| `augent help` | Show full help |

---

## Web UI

Visual interface for manual use. Runs 100% locally - no cloud APIs, no Claude credits.

```bash
python3 -m augent.web
```

Open: **http://127.0.0.1:9797**

1. **Upload** an audio file (MP3, WAV, M4A, etc.)
2. **Enter keywords** separated by commas
3. **Click SEARCH**
4. **View results** with clickable timestamps

| Command | Description |
|---------|-------------|
| `python3 -m augent.web` | Start on port 9797 |
| `python3 -m augent.web --port 3000` | Custom port |
| `python3 -m augent.web --share` | Create public link |

---

## Why Augent?

Claude Code agents can now:
- **Learn from video tutorials** without watching - search for specific techniques instantly
- **Find exact instructions** using proximity search (e.g., "install" near "dependencies")
- **Batch process** entire tutorial libraries in parallel
- **Extract audio clips** around key moments
- **Cache everything** - no re-transcription needed

Built on [faster-whisper](https://github.com/guillaumekln/faster-whisper) for 2-4x faster transcription than original Whisper.

## Agentic Use Cases

### Learn Any Skill from Tutorials

Download tutorials, let Claude find what you need:

```
1. Download 10 Roblox game dev tutorials
2. Ask Claude: "How do I add multiplayer?"
3. Claude searches all 10, finds the exact timestamps
4. Claude reads the instructions and executes them
```

### Batch Tutorial Processing

Process entire course libraries at once:

```bash
# Download a playlist of tutorials
audio-downloader "url1" "url2" "url3"

# Search all for specific techniques
augent search "tutorials/*.webm" "authentication,API,database" --workers 4
```

### Multi-Agent Learning Workflows

Assign tutorial analysis to worker agents:
- **Agent A**: Download and transcribe tutorial library
- **Agent B**: Search for specific techniques, extract instructions
- **Agent C**: Execute the found instructions in your codebase

### Course Summarization

Turn 10-hour courses into searchable knowledge:

```bash
# Transcribe entire course
augent transcribe course.mp3 --format json --output course.json

# Search for any topic instantly
augent search course.mp3 "error handling,debugging,testing"
```

### Research & Documentation

Extract structured information from video documentation, conference talks, or technical deep-dives for reference materials.

### Clawdbot Integration

[Clawdbot](https://github.com/clawdbot/clawdbot) is a personal AI assistant that runs locally and connects to WhatsApp, Telegram, X, Slack, Discord, iMessage, and more. With Augent, your Clawdbot gains ears.

**Multi-Source Video Research**

Text Clawdbot on any messaging platform:

> "Here are 5 YC founder interviews. What patterns do they share about getting first customers?"
> [URL1] [URL2] [URL3] [URL4] [URL5]

Clawdbot will:
1. Download all 5 with `audio-downloader`
2. Batch search "first customers" "early users" "traction" across all videos
3. Find relevant segments with timestamps
4. Synthesize patterns and reply:

**Pattern 1: Do things that don't scale**
Mentioned in 4 of 5 interviews
- *"We literally delivered the first orders ourselves..."* — Interview 1 at 12:34
- *"I was manually onboarding every single user..."* — Interview 3 at 8:22

**Pattern 2: Solve your own problem**
Mentioned in 3 of 5 interviews
- *"I built it because I needed it for my own workflow..."* — Interview 2 at 5:11

**Pattern 3: Launch before you're ready**
Mentioned in 3 of 5 interviews
- *"We shipped with bugs everywhere, didn't matter..."* — Interview 4 at 18:45

**Why this matters:**
- **Research from any channel** — Ask questions on WhatsApp, get video insights
- **Multi-source search** — Query across 10 videos at once, not just one
- **Patterns, not transcripts** — Get synthesized insights with timestamps
- **All local** — Your queries and content never leave your machine

## CLI Usage

```bash
# Basic search
augent search tutorial.mp3 "install,setup,configure"

# Better accuracy
augent search tutorial.mp3 "keyword" --model small

# Batch processing
augent search "tutorials/*.mp3" "authentication,API" --workers 4

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

## audio-downloader

A speed-optimized audio downloader built by Augent. Downloads audio ONLY from any video URL at lightning speed.

```bash
audio-downloader "https://youtube.com/watch?v=xxx"
```

**Default:** Saves to `~/Downloads`. Use `-o` to change output folder.

**Speed Optimizations:**
- aria2c multi-connection downloads (16 parallel connections)
- Concurrent fragment downloading (4 fragments)
- No video download - audio extraction only
- No format conversion - native audio format for maximum speed

**Supports:** YouTube, Vimeo, SoundCloud, Twitter, TikTok, and 1000+ sites

```bash
# Download to ~/Downloads (default)
audio-downloader "https://youtube.com/watch?v=xxx"

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

## Python API

```python
from augent import search_audio, transcribe_audio, search_audio_proximity

# Basic keyword search
results = search_audio("tutorial.mp3", ["install", "setup"])
# {"install": [{"timestamp": "2:34", "snippet": "...first install the dependencies..."}]}

# Full transcription
transcription = transcribe_audio("tutorial.mp3", model_size="small")

# Proximity search
matches = search_audio_proximity(
    "tutorial.mp3",
    keyword1="error",
    keyword2="fix",
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

# Open browser: http://127.0.0.1:9797

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
- Very heavy accents or extremely poor audio quality
- Medical/legal transcriptions requiring maximum accuracy

**Warning:** `medium` and `large` models are very CPU/memory intensive. They can freeze or overheat lower-spec machines (like MacBook Air). Stick to `tiny` or `base` unless you have a powerful machine with good cooling.

`tiny` handles tutorials, interviews, lectures, ads with background music, and almost everything else perfectly fine.

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
- [Clawdbot](https://github.com/clawdbot/clawdbot)
- [Ralph-Wiggum Plugin](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum)
- [Gas Town](https://github.com/steveyegge/gastown)
