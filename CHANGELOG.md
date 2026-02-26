# Changelog

All notable changes to Augent are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2026.2.26] - 2026-02-26

### Added

- **`search_memory` tool** — search across ALL stored transcriptions in one query, no audio_path needed
- **Keyword and semantic modes** — `search_memory` defaults to literal keyword matching; opt into meaning-based search with `mode: "semantic"`
- **CSV export** — optional `output` parameter on `search_memory` saves results as a CSV file
- **25-word snippets** — all search tools now return consistent ~25-word context snippets with keyword highlighting

### Improved

- **Keyword highlighting** — matched keywords shown in **bold** across all search results (search_audio, deep_search, search_memory, search_proximity)
- **CLI** — `augent memory search "query"` with `--semantic` and `--top-k` flags

---

## [2026.2.21] - 2026-02-21

### Changed

- **"Cache" rebranded to "Memory"** — tools, CLI commands, code, and docs now use "memory" language (`list_memories`, `memory_stats`, `clear_memory`, `augent memory`)

### Improved

- **Installer UX** — animated spinners, paced output, and race condition fix for `curl|bash` piped installs
- **ASCII banner** for CLI and installer using pyfiglet

---

## [2026.2.16] - 2026-02-16

### Added

- **OpenClaw integration** — skill package for ClawHub + `augent setup openclaw` one-liner
- **Installer auto-detects OpenClaw** and configures MCP alongside Claude
- **MCP protocol tests** — 33 tests covering routing, tool listing, and error handling

---

## [2026.2.15] - 2026-02-15

### Fixed

- **TTS no longer blocks MCP** — runs in background subprocess with job polling
- Installer correctly selects framework Python for MCP config on macOS

---

## [2026.2.14] - 2026-02-14

### Improved

- **Quiz checkbox syntax** — answer options render as Obsidian checkboxes
- Answer key formatting enforced (bold number + letter, em dash, explanation)
- Claude always routes video URLs through `take_notes`, never WebFetch

---

## [2026.2.13] - 2026-02-13

### Added

- **`save_content` mode for `take_notes`** — bypasses Write tool, ensures post-processing runs
- Installer auto-installs Python 3.12 when only 3.13 is available

### Fixed

- Installer eliminates silent failures and verifies all packages
- `take_notes` embeds absolute file paths in Claude instructions
- Skip re-downloading dependencies on reinstall

---

## [2026.2.12] - 2026-02-12

### Improved

- **Lazy imports** for optional dependencies — installing mid-session works without restart
- Preserve WAV file when ffmpeg conversion fails in TTS

---

## [2026.2.9] - 2026-02-09

### Added

- **Text-to-speech** — Kokoro TTS with 54 voices across 9 languages
- **`read_aloud` option** for `take_notes` — generates spoken MP3 and embeds in Obsidian

---

## [2026.2.8] - 2026-02-08

### Added

- **`identify_speakers`** — speaker diarization, no API keys required
- **`deep_search`** — semantic search using sentence-transformers (find by meaning, not keywords)
- **`chapters`** — auto-detect topic boundaries with embedding similarity
- **5 note styles** for `take_notes`: tldr, notes, highlight, eye-candy, quiz
- **Obsidian .txt integration guide** — full setup for live-synced notes

### Changed

- Renamed `list_audio_files` → `list_files`, defaults to all common media formats
- Enforced `tiny` as default model across all tool schemas

---

## [2026.2.7] - 2026-02-07

### Added

- **`take_notes` tool** — one-click URL to formatted notes pipeline (download + transcribe + save .txt)

---

## [2026.1.31] - 2026-01-31

### Added

- **Title-based cache lookups** — search cached transcriptions by name
- **Markdown transcription files** — each cached transcription also saved as readable `.md`

---

## [2026.1.29] - 2026-01-29

### Changed

- **Python 3.10+ required** (dropped 3.9 support)

### Fixed

- Homebrew Python compatibility (PATH, PEP 668, absolute paths)
- Pinned yt-dlp to stable version for reliable downloads
- Installer handles Homebrew permission issues gracefully

---

## [2026.1.26] - 2026-01-26

### Added

- **`audio-downloader` CLI tool** — speed-optimized with aria2c (16 parallel connections)
- **`download_audio` MCP tool** — Claude can download audio directly
- Model size warnings for medium/large (resource-intensive)

### Fixed

- aria2c downloader-args format causing download failures
- Web UI default port changed from 8888 to 9797

---

## [2026.1.24] - 2026-01-24

### Added

- **Web UI v1** — polished Gradio interface with failproof startup
- **CI/CD** — GitHub Actions testing on Python 3.10, 3.11, 3.12
- **Professional installer** — one-liner `curl | bash` setup
- Logo and branding

---

## [2026.1.23] - 2026-01-23

### Added

- **Initial release**
- **MCP server** exposing tools for Claude Code and Claude Desktop
- **Transcription engine** powered by faster-whisper with word-level timestamps
- **Keyword search** with timestamped matches and context snippets
- **Proximity search** — find where keywords appear near each other
- **Batch processing** — search multiple files in parallel
- **Three-layer caching** — transcriptions, embeddings, and diarization in SQLite
- **CLI** with search, transcribe, proximity, and cache management commands
- **Export formats** — JSON, CSV, SRT, VTT, Markdown
- **Cross-platform support** — macOS, Linux, Windows
