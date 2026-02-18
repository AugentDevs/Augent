# Augent — Audio + Agents

<p align="center">
  <picture>
    <img src="./images/logo.png" width="600" alt="Augent">
  </picture>
</p>

<p align="center">
  <strong>Hours of content, seconds to find it. Fully local, fully private.</strong>
</p>

<p align="center">
  <a href="https://github.com/AugentDevs/Augent/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/AugentDevs/Augent/tests.yml?label=build&color=00F060&style=for-the-badge" alt="Build"></a>
  <img src="https://img.shields.io/badge/dynamic/toml?url=https://raw.githubusercontent.com/AugentDevs/Augent/main/pyproject.toml&query=$.project.version&label=version&color=00F060&style=for-the-badge" alt="Version">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-00F060.svg?style=for-the-badge" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-00F060.svg?style=for-the-badge" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#mcp-tools">MCP Tools</a> ·
  <a href="#cli">CLI</a> ·
  <a href="#web-ui">Web UI</a> ·
  <a href="https://docs.augent.app">Docs</a>
</p>

**Augent** is an MCP server that gives agents audio intelligence — the ability to download, transcribe, search, and analyze content from any URL, entirely on your machine. Point it at any video, podcast, lecture, or recording and it indexes every word. Search by keyword, by speaker, by topic, or by _meaning_. Identify who's talking, break content into chapters, take formatted notes, and read them back with text-to-speech. You install it once, and every agent gains access to a growing suite of tools that turn any media into actionable intelligence.

One install, full pipeline — from raw URL to actionable insight in a single prompt. Every transcription is cached permanently; the first run processes, every search after that is instant. Batch process entire libraries in one prompt with no file limit. Market research, competitive analysis, content repurposing, due diligence, education — if it's hidden in content form, Augent finds it. Built for Claude Code. Compatible with any MCP client.

[Website](https://augent.app) · [Docs](https://docs.augent.app) · [Getting Started](https://docs.augent.app/getting-started) · [Tool Reference](https://docs.augent.app/tools/download-audio) · [Changelog](CHANGELOG.md)

Preferred setup: run the one-line installer in your terminal.
The installer handles Python, FFmpeg, yt-dlp, aria2, and all dependencies automatically.
Works on **macOS and Linux**. Windows users can install via pip.
New install? Start here: [Getting Started](https://docs.augent.app/getting-started)

<br />

## Install

```bash
curl -fsSL https://augent.app/install.sh | bash
```

Works on macOS and Linux. Installs everything automatically.

**Windows:** `pip install "augent[all] @ git+https://github.com/AugentDevs/Augent.git"`

<br />

<p align="center">
  <img src="./images/augent.gif" alt="Watch Nothing. Find Everything.">
</p>

<br />

## How It Works

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    A["URL / File"] --> B["Download"]
    B --> C["Transcribe"]
    C --> D["Cache"]
    D --> E["Search"]
    D --> F["Analyze"]
    D --> G["Export"]

    E --> E1["Keyword"]
    E --> E2["Semantic"]
    E --> E3["Batch"]
    E --> E4["Proximity"]

    F --> F1["Speaker ID"]
    F --> F2["Chapters"]
    F --> F3["Notes"]

    G --> G1["Text to Speech"]
```

## Project Structure

```
augent/
├── mcp.py          # MCP server — tools for Claude
├── core.py         # Transcription engine (faster-whisper)
├── search.py       # Keyword search
├── embeddings.py   # Semantic search + chapters
├── speakers.py     # Speaker diarization
├── tts.py          # Text-to-speech (Kokoro)
├── cache.py        # Three-layer caching (SQLite)
├── cli.py          # CLI interface
├── web.py          # Web UI (Gradio)
├── export.py       # Export formats (JSON, CSV, SRT, VTT, MD)
└── clips.py        # Audio clip extraction
```

<br />

## MCP Tools

The primary way to use Augent. Claude Code gets direct access to all 14 audio intelligence tools.

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

| Tool | Description |
|:-----|:------------|
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

<details>
<summary>Example prompt</summary>

> *"Download these 10 podcasts and find every moment a host covers a product in a positive or unique way. Not just brand mentions, only real endorsements or life-changing recommendations. Give me the timestamps and exactly what they said: url1, url2, url3, url4, url5, url6, url7, url8, url9, url10"*

<p align="center">
  <img src="./images/pipeline.png" alt="Augent Pipeline — From URLs to insights in one prompt" width="100%">
</p>

</details>

<br />

## CLI

For terminal-based usage. Works standalone or inside Claude Code.

![Augent CLI](./images/cli-help.png)

| Command | Description |
|:--------|:------------|
| `audio-downloader "URL"` | Download audio from video URL (speed-optimized) |
| `augent search audio.mp3 "keyword"` | Search for keywords |
| `augent transcribe audio.mp3` | Full transcription |
| `augent proximity audio.mp3 "A" "B"` | Find keyword A near keyword B |
| `augent cache stats` | View cache statistics |
| `augent cache list` | List cached transcriptions |
| `augent cache clear` | Clear cache |

<br />

## Web UI

Visual interface for manual use. Runs 100% locally — no internet required.

```bash
python3 -m augent.web
```

Open: **http://127.0.0.1:9797**

1. **Upload** an audio file (MP3, WAV, M4A, etc.)
2. **Enter keywords** separated by commas
3. **Click SEARCH**
4. **View results** with timestamps and context

<details>
<summary>Web UI options</summary>

| Command | Description |
|:--------|:------------|
| `python3 -m augent.web` | Start on port 9797 |
| `python3 -m augent.web --port 3000` | Custom port |
| `python3 -m augent.web --share` | Create public link |

</details>

![Augent Web UI - Upload](./images/webui-1.png)
![Augent Web UI - Results](./images/webui-2.png)

<br />

## Model Sizes

**`tiny` is the default** and handles nearly everything. Use `small` or above only for heavy accents, poor audio, or lyrics.

| Model | Speed | Accuracy |
|:------|:------|:---------|
| **tiny** | Fastest | Excellent (default) |
| base | Fast | Excellent |
| small | Medium | Superior |
| medium | Slow | Outstanding |
| large | Slowest | Maximum |

<br />

## Contributing

PRs welcome. Open an [issue](https://github.com/AugentDevs/Augent/issues) for bugs or feature requests.

<br />

## License

MIT
