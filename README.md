<p align="center">
  <img src="./images/logo.png" width="150" alt="Augent Logo">
</p>

<h1 align="center">Augent</h1>

<p align="center">
  <a href="https://github.com/AugentDevs/Augent/releases/latest"><img src="https://img.shields.io/github/v/release/AugentDevs/Augent?color=%2300f060" alt="Release"></a>
  <a href="https://github.com/AugentDevs/Augent/actions/workflows/tests.yml"><img src="https://github.com/AugentDevs/Augent/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20·%20Linux%20·%20Windows-lightgrey.svg" alt="Platform">
</p>

<p align="center"><strong>Audio intelligence for Claude Code agents and agentic swarms</strong><br>Built by <a href="https://augent.app">Augent</a></p>

<p align="center">An MCP plugin that searches any content the way you search text<br>by speaker, keyword, or topic. Hours of content, seconds to find it.<br>Fully local, fully private.</p>

---

## Install

```bash
curl -fsSL https://augent.app/install.sh | bash
```

Works on macOS and Linux. Installs everything automatically.

**Windows:** `pip install "augent[all] @ git+https://github.com/AugentDevs/Augent.git"`

**Requires:** Python 3.9+, [FFmpeg](https://ffmpeg.org/), [aria2](https://aria2.github.io/) (the install script handles all of this)

**[Documentation](https://docs.augent.app)** — Full reference for all tools, CLI commands, and API

---

<p align="center">
  <img src="./images/augent.gif" alt="Watch Nothing. Find Everything.">
</p>

---

## Usage

| Mode | Best For |
|------|----------|
| **Claude Code (MCP)** | Agentic workflows with all 14 tools — one prompt does everything |
| **CLI** | Terminal-based searches and batch processing |
| **Web UI** | Visual interface for manual uploads and searches — runs 100% locally |

---

## Claude Code (MCP)

The primary way to use Augent. Claude Code gets direct access to all 14 audio intelligence tools.

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

| Tool | Description |
|------|-------------|
| `download_audio` | Download audio from video URLs at maximum speed (YouTube, Vimeo, TikTok, etc.) |
| `transcribe_audio` | Full transcription with metadata |
| `search_audio` | Find keywords with timestamps and context snippets |
| `deep_search` | Search audio by meaning, not just keywords (semantic search) |
| `take_notes` | Take notes from any URL with style presets |
| `chapters` | Auto-detect topic chapters in audio with timestamps |
| `batch_search` | Search multiple files in parallel (for swarms) |
| `text_to_speech` | Convert text to natural speech audio (Kokoro TTS, 54 voices, 9 languages) |
| `search_proximity` | Find where keywords appear near each other |
| `identify_speakers` | Identify who speaks when in audio (speaker diarization) |
| `list_files` | List media files in a directory |
| `list_cached` | List cached transcriptions by title |
| `cache_stats` | View transcription cache statistics |
| `clear_cache` | Clear cached transcriptions |

**[Full tool reference →](https://docs.augent.app/tools/download-audio)**

### Examples

**Notes + voice:**
> *"Take notes from this lecture and read them back to me as audio: https://youtube.com/watch?v=..."*

**Ad angle research:**
> *"Download these 5 podcasts and find every moment a host covers a product in a positive or unique way. Not just brand mentions, only real endorsements or life-changing recommendations. Give me the timestamps and exactly what they said: url1, url2, url3, url4, url5"*

---

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
4. **View results** with timestamps and context

| Command | Description |
|---------|-------------|
| `python3 -m augent.web` | Start on port 9797 |
| `python3 -m augent.web --port 3000` | Custom port |
| `python3 -m augent.web --share` | Create public link |

![Augent Web UI - Upload](./images/webui-1.png)
![Augent Web UI - Results](./images/webui-2.png)

---

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

---

## Export Formats

- **JSON** - Structured data, grouped by keyword
- **CSV** - Spreadsheet-ready
- **SRT** - SubRip subtitles
- **VTT** - WebVTT for web video
- **Markdown** - Human-readable reports

---

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

---

## Contributing

PRs welcome. Open an [issue](https://github.com/AugentDevs/Augent/issues) for bugs or feature requests.

---

## License

MIT License - see [LICENSE](LICENSE) for details.
