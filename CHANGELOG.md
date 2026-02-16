# Changelog

All notable changes to Augent are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2025-01-23

### Added

- **MCP server** with 14 tools for Claude Code and Claude Desktop integration
- **Transcription engine** powered by faster-whisper with word-level timestamps
- **Keyword search** with timestamped matches and context snippets
- **Semantic search** using sentence-transformers — find moments by meaning, not just keywords
- **Auto-chapters** — detect topic boundaries with embedding similarity
- **Speaker diarization** — identify who speaks when, no API keys required
- **Text-to-speech** — Kokoro TTS with 54 voices across 9 languages
- **Note-taking** — download, transcribe, and format notes from any URL in 5 styles (tldr, notes, highlight, eye-candy, quiz)
- **Batch processing** — search multiple files in parallel for agentic swarms
- **Proximity search** — find where keywords appear near each other
- **Audio downloader** — speed-optimized with aria2c multi-connection downloads
- **Three-layer caching** — transcriptions, embeddings, and diarization cached in SQLite
- **CLI** with search, transcribe, proximity, and cache management commands
- **Web UI** — Gradio-based visual interface running 100% locally
- **Cross-platform installer** — one-liner setup for macOS and Linux
- **Export formats** — JSON, CSV, SRT, VTT, Markdown

## [1.0.1] - 2025-02-15

### Added

- **OpenClaw integration** — skill package for ClawHub + `augent setup openclaw` one-liner
- **Installer auto-detects OpenClaw** and configures MCP alongside Claude

### Fixed

- TTS no longer blocks the MCP connection (runs in background subprocess)
- Installer correctly selects framework Python for MCP config on macOS
- Quiz formatting preserves checkbox syntax for Obsidian
