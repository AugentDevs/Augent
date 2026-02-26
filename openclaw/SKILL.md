---
name: augent
description: Audio intelligence toolkit. Transcribe, search by keyword or meaning, take notes, detect chapters, identify speakers, and text-to-speech — all local, all private. All MCP tools for audio.
homepage: https://github.com/AugentDevs/Augent
metadata: {"openclaw":{"emoji":"🎙","requires":{"bins":["augent-mcp","ffmpeg"]},"install":[{"id":"uv","kind":"uv","package":"augent","bins":["augent-mcp","augent","augent-web"],"label":"Install augent (uv)"}]}}
---

# Augent — Audio Intelligence for AI Agents

Augent is an MCP server that gives your agent all audio intelligence tools. Transcribe, search, take notes, identify speakers, detect chapters, and generate speech — fully local, fully private.

## Config

```json
{
  "mcp": {
    "servers": {
      "augent": {
        "command": "augent-mcp"
      }
    }
  }
}
```

If `augent-mcp` is not in PATH, use the full Python module path:

```json
{
  "mcp": {
    "servers": {
      "augent": {
        "command": "python3",
        "args": ["-m", "augent.mcp"]
      }
    }
  }
}
```

## Install

**One-liner (recommended):** Installs augent, FFmpeg, yt-dlp, aria2, and configures MCP automatically.

```bash
curl -fsSL https://augent.app/install.sh | bash
```

**Via uv:**

```bash
uv tool install augent
```

For all features (semantic search, speaker diarization, TTS):

```bash
uv tool install "augent[all]"
```

**Via pip:**

```bash
pip install "augent[all]"
```

**System dependencies:** FFmpeg is required. Install with `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux). For fast audio downloads, also install yt-dlp and aria2.

## Tools

Augent exposes all these MCP tools:

### Core

| Tool | Description |
|------|-------------|
| `download_audio` | Download audio from video URLs at maximum speed. Supports YouTube, Vimeo, TikTok, Twitter/X, SoundCloud, and 1000+ sites. Uses aria2c multi-connection + concurrent fragments. |
| `transcribe_audio` | Full transcription of any audio file with timestamps. Returns text, language, duration, and segment count. Results are cached by file hash. |
| `search_audio` | Search audio for keywords. Returns timestamped matches with context snippets. |
| `deep_search` | Semantic search — find moments by meaning, not just keywords. Uses sentence-transformers embeddings. |
| `take_notes` | All-in-one: download audio from URL, transcribe, and save formatted notes. Supports 5 styles: tldr, notes, highlight, eye-candy, quiz. |

### Analysis

| Tool | Description |
|------|-------------|
| `chapters` | Auto-detect topic chapters with timestamps using embedding similarity. |
| `search_proximity` | Find where two keywords appear near each other (e.g., "startup" within 30 words of "funding"). |
| `identify_speakers` | Speaker diarization — identify who speaks when. No API keys required. |
| `batch_search` | Search multiple audio files in parallel. Ideal for podcast libraries or interview collections. |

### Utilities

| Tool | Description |
|------|-------------|
| `text_to_speech` | Convert text to natural speech using Kokoro TTS. 54 voices, 9 languages. Runs in background. |
| `list_files` | List media files in a directory with size info. |
| `list_cached` | Browse all cached transcriptions by title, duration, and date. |
| `cache_stats` | View cache statistics (file count, total duration). |
| `clear_cache` | Clear the transcription cache to free disk space. |

## Usage Examples

### Take notes from a video

> "Take notes from https://youtube.com/watch?v=xxx"

The agent calls `take_notes` which downloads, transcribes, and returns formatted notes. One tool call does everything.

### Search a podcast for topics

> "Search this podcast for every mention of AI regulation" — provide the file path or URL.

The agent uses `search_audio` for exact keyword matches, or `deep_search` for semantic matches (finds relevant discussion even without exact words).

### Transcribe and identify speakers

> "Transcribe this meeting recording and tell me who said what"

The agent calls `transcribe_audio` then `identify_speakers` to label each segment by speaker.

### Search across multiple files

> "Search all my downloaded podcasts for discussions about climate policy"

The agent uses `list_files` to find audio files, then `batch_search` to search them all in parallel.

### Generate speech from text

> "Read these notes aloud"

The agent calls `text_to_speech` to generate an MP3 with natural speech. Supports multiple voices and languages.

## Note Styles

When using `take_notes`, the `style` parameter controls formatting:

| Style | Description |
|-------|-------------|
| `tldr` | Shortest possible summary. One screen. Bold key terms. |
| `notes` | Clean sections with nested bullets (default). |
| `highlight` | Notes with callout blocks for key insights and blockquotes with timestamps. |
| `eye-candy` | Maximum visual formatting — callouts, tables, checklists, blockquotes. |
| `quiz` | Multiple-choice questions with answer key. |

## Model Sizes

`tiny` is the default and handles nearly everything. Only use larger models for heavy accents, poor audio quality, or maximum accuracy needs.

| Model | Speed | Accuracy |
|-------|-------|----------|
| **tiny** | Fastest | Excellent (default) |
| base | Fast | Excellent |
| small | Medium | Superior |
| medium | Slow | Outstanding |
| large | Slowest | Maximum |

## Caching

Transcriptions are cached by file content hash + model size. Same file = instant results on repeat searches. Cache persists at `~/.augent/cache/transcriptions.db`. Use `cache_stats` to check usage and `clear_cache` to free space.

## Requirements

- Python 3.10+
- FFmpeg (audio processing)
- yt-dlp + aria2 (optional, for audio downloads)

## Links

- [GitHub](https://github.com/AugentDevs/Augent)
- [Documentation](https://docs.augent.app)
- [Install Script](https://augent.app/install.sh)
