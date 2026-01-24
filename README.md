# Augent Plugin

**Audio intelligence for Claude Code agents and agentic swarms** Built by [Augent](https://augent.app)

An MCP-powered plugin that gives Claude Code the ability to transcribe, search, and analyze audio files locally. Perfect for agentic automation loops like [Ralph-Wiggum](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) and [Gas Town](https://github.com/steveyegge/gastown).

---

## User Manual

### Step 1: Install

```bash
git clone https://github.com/AugentDevs/Augent.git
cd Augent
pip install -e .[web]
```

Requires Python 3.9+ and FFmpeg.

**Don't have FFmpeg?**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

### Step 2: Run Web UI

```bash
python3 -m augent.web
```

Open your browser to: **http://127.0.0.1:8888**

### Step 3: Use It

1. **Upload** an audio file (MP3, WAV, M4A, etc.)
2. **Enter keywords** separated by commas (e.g., `money, success, growth`)
3. **Click SEARCH**
4. **View results** with timestamps - click any timestamp to jump to that moment

### Commands Reference

| Command | Description |
|---------|-------------|
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
git clone https://github.com/AugentDevs/Augent.git
cd Augent
pip install -e .[web]
python3 -m augent.web
```

Open browser: **http://127.0.0.1:8888**

Verify CLI: `augent help`

## Claude Code Setup

Add to your Claude Code project (`.mcp.json` in project root):

```json
{
  "mcpServers": {
    "augent": {
      "command": "augent-mcp"
    }
  }
}
```

Or for Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "augent": {
      "command": "python",
      "args": ["-m", "augent.mcp"]
    }
  }
}
```

## MCP Tools

Once configured, Claude has access to:

| Tool | Description |
|------|-------------|
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

## CLI Usage

```bash
# Basic search
augent search audio.mp3 "money,success,growth"

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
results = search_audio("podcast.mp3", ["money", "success"])
# {"money": [{"timestamp": "2:34", "snippet": "...talking about money..."}]}

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

<img width="2002" height="1018" alt="Web_UI_demo-1_1_80" src="https://github.com/user-attachments/assets/5487b6b0-4966-4667-9b01-30e0488a6551" />
<img width="2002" height="1018" alt="Web_UI_demo-2_80" src="https://github.com/user-attachments/assets/a7b6c9c0-4cf0-41c8-b0fb-047c78be34ad" />

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
