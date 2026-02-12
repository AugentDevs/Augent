"""
Augent MCP Server

Model Context Protocol server for Claude Desktop and Claude Code integration.
Exposes Augent as a native tool that Claude can call directly.

Tools exposed:
- download_audio: Download audio from video URLs (YouTube, etc.) at maximum speed
- transcribe_audio: Full transcription without keyword search
- search_audio: Search for keywords in audio files
- deep_search: Semantic search by meaning, not just keywords
- take_notes: All-in-one note-taking: download + transcribe + save .txt to Desktop
- chapters: Auto-detect topic chapters in audio
- batch_search: Search multiple audio files in parallel
- text_to_speech: Convert text to natural speech audio using Kokoro TTS
- search_proximity: Find keywords appearing near each other
- identify_speakers: Speaker diarization (who said what)
- list_files: List media files in a directory
- list_cached: List all cached transcriptions
- cache_stats: View cache statistics
- clear_cache: Clear transcription cache

Usage:
  python -m augent.mcp
  # or
  augent-mcp

Add to Claude Code project (.mcp.json):
  {
    "mcpServers": {
      "augent": {
        "command": "augent-mcp"
      }
    }
  }

Add to Claude Desktop config (claude_desktop_config.json):
  {
    "mcpServers": {
      "augent": {
        "command": "python",
        "args": ["-m", "augent.mcp"]
      }
    }
  }
"""

import sys
import json
from typing import Any

# Check for required dependencies before importing
_MISSING_DEPS = []
try:
    import faster_whisper
except ImportError:
    _MISSING_DEPS.append("faster-whisper")

try:
    import torch
except ImportError:
    _MISSING_DEPS.append("torch")

if _MISSING_DEPS:
    def _dependency_error():
        return {
            "error": f"Missing dependencies: {', '.join(_MISSING_DEPS)}. "
                     f"Install with: pip install {' '.join(_MISSING_DEPS)}"
        }
    # Create stub functions that return errors
    def search_audio(*args, **kwargs):
        raise RuntimeError(_dependency_error()["error"])
    def search_audio_full(*args, **kwargs):
        raise RuntimeError(_dependency_error()["error"])
    def transcribe_audio(*args, **kwargs):
        raise RuntimeError(_dependency_error()["error"])
    def search_audio_proximity(*args, **kwargs):
        raise RuntimeError(_dependency_error()["error"])
    def get_cache_stats():
        return _dependency_error()
    def clear_cache():
        return 0
    def list_cached():
        return []
else:
    from .core import (
        search_audio,
        search_audio_full,
        transcribe_audio,
        search_audio_proximity,
        get_cache_stats,
        clear_cache,
        list_cached
    )

# Optional dependencies (sentence-transformers, simple-diarizer, kokoro)
# are imported lazily inside handler functions so that installing them
# mid-session works without restarting the MCP server.


def send_response(response: dict) -> None:
    """Send JSON-RPC response to stdout."""
    output = json.dumps(response)
    sys.stdout.write(output + "\n")
    sys.stdout.flush()


def send_error(id: Any, code: int, message: str) -> None:
    """Send JSON-RPC error response."""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    })


def handle_initialize(id: Any, params: dict) -> None:
    """Handle initialize request."""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "augent",
                "version": "1.0.0"
            }
        }
    })


def handle_tools_list(id: Any) -> None:
    """Handle tools/list request."""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "result": {
            "tools": [
                {
                    "name": "download_audio",
                    "description": "Download audio from video URLs at maximum speed. Built by Augent with speed optimizations (aria2c multi-connection, concurrent fragments). Downloads audio ONLY - never video. Supports YouTube, Vimeo, TikTok, Twitter, SoundCloud, and 1000+ sites.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Video URL to download audio from (YouTube, Vimeo, TikTok, etc.)"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Directory to save the audio file. Default: ~/Downloads"
                            }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "transcribe_audio",
                    "description": "Transcribe an audio file and return the full text with timestamps. Useful when you need the complete transcription rather than searching for specific keywords.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            }
                        },
                        "required": ["audio_path"]
                    }
                },
                {
                    "name": "search_audio",
                    "description": "Search audio files for keywords and return timestamped matches with context snippets. Useful for finding specific moments in podcasts, interviews, lectures, or any audio content.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file (MP3, WAV, M4A, etc.)"
                            },
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of keywords or phrases to search for"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            },
                            "include_full_text": {
                                "type": "boolean",
                                "description": "Include full transcription text in response. Default: false"
                            }
                        },
                        "required": ["audio_path", "keywords"]
                    }
                },
                {
                    "name": "deep_search",
                    "description": "Search audio by meaning, not just keywords.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file"
                            },
                            "query": {
                                "type": "string",
                                "description": "Natural language search query (e.g. 'discussion about funding challenges')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return. Default: 5"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            }
                        },
                        "required": ["audio_path", "query"]
                    }
                },
                {
                    "name": "take_notes",
                    "description": "Take notes from a URL. Saves .txt to Desktop.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Video/audio URL to take notes from (YouTube, Vimeo, TikTok, Twitter, SoundCloud, etc.)"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Directory to save the .txt notes file. Default: ~/Desktop"
                            },
                            "style": {
                                "type": "string",
                                "enum": ["tldr", "notes", "highlight", "eye-candy", "quiz"],
                                "description": "Note style. tldr > notes > highlight > eye-candy increases formatting richness. quiz generates questions. Default: notes. Pick based on what the user asks for."
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            },
                            "read_aloud": {
                                "type": "boolean",
                                "description": "Generate a spoken audio summary and embed it in the notes for Obsidian playback. Default: false"
                            }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "chapters",
                    "description": "Auto-detect topic chapters in audio.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file"
                            },
                            "sensitivity": {
                                "type": "number",
                                "description": "0.0 = many chapters, 1.0 = few chapters. Default: 0.4"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            }
                        },
                        "required": ["audio_path"]
                    }
                },
                {
                    "name": "batch_search",
                    "description": "Search multiple audio files for keywords in parallel. Ideal for processing podcast libraries, interview collections, or any batch of audio files. Returns aggregated results with file paths.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of paths to audio files"
                            },
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of keywords or phrases to search for"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            },
                            "workers": {
                                "type": "integer",
                                "description": "Number of parallel workers. Default: 2"
                            }
                        },
                        "required": ["audio_paths", "keywords"]
                    }
                },
                {
                    "name": "text_to_speech",
                    "description": "Convert text to natural speech audio using Kokoro TTS. Saves an MP3 file. Pass text for raw TTS, or file_path to read a notes file (strips markdown, skips metadata, embeds audio player).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to convert to speech. Either text or file_path is required."
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to a notes file to read aloud. Strips markdown formatting, skips metadata, generates MP3, and embeds audio player in the file."
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice ID. American English: af_heart (female, default), af_bella, af_nicole, af_nova, af_sky, am_adam (male), am_eric, am_michael. British English: bf_emma, bf_lily, bm_daniel, bm_george. Also supports Spanish, French, Japanese, Chinese voices."
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Directory to save the MP3 file. Default: ~/Desktop"
                            },
                            "output_filename": {
                                "type": "string",
                                "description": "Custom filename. Auto-generated if not set."
                            },
                            "speed": {
                                "type": "number",
                                "description": "Speech speed multiplier. Default: 1.0"
                            }
                        }
                    }
                },
                {
                    "name": "search_proximity",
                    "description": "Find where one keyword appears near another keyword in audio. Useful for finding contextual discussions, e.g., 'startup' near 'funding'.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file"
                            },
                            "keyword1": {
                                "type": "string",
                                "description": "Primary keyword to find"
                            },
                            "keyword2": {
                                "type": "string",
                                "description": "Secondary keyword that must appear nearby"
                            },
                            "max_distance": {
                                "type": "integer",
                                "description": "Maximum number of words between keywords. Default: 30"
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            }
                        },
                        "required": ["audio_path", "keyword1", "keyword2"]
                    }
                },
                {
                    "name": "identify_speakers",
                    "description": "Identify who speaks when in audio.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Path to the audio file"
                            },
                            "num_speakers": {
                                "type": "integer",
                                "description": "Number of speakers if known. Auto-detects if not set."
                            },
                            "model_size": {
                                "type": "string",
                                "enum": ["tiny", "base", "small", "medium", "large"],
                                "description": "Whisper model size. ALWAYS use tiny unless the user explicitly requests a different size. tiny is already highly accurate."
                            }
                        },
                        "required": ["audio_path"]
                    }
                },
                {
                    "name": "list_files",
                    "description": "List media files in a directory.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory path to search"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern for matching files. Default: all common media formats"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Search subdirectories. Default: false"
                            }
                        },
                        "required": ["directory"]
                    }
                },
                {
                    "name": "list_cached",
                    "description": "List all cached transcriptions with their titles, durations, dates, and file paths to markdown files. Useful for browsing what has already been transcribed.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "cache_stats",
                    "description": "View transcription cache statistics including number of cached files and total duration.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "clear_cache",
                    "description": "Clear the transcription cache to free disk space.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
            ]
        }
    })


def handle_tools_call(id: Any, params: dict) -> None:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "download_audio":
            result = handle_download_audio(arguments)
        elif tool_name == "transcribe_audio":
            result = handle_transcribe_audio(arguments)
        elif tool_name == "search_audio":
            result = handle_search_audio(arguments)
        elif tool_name == "deep_search":
            result = handle_deep_search(arguments)
        elif tool_name == "take_notes":
            result = handle_take_notes(arguments)
        elif tool_name == "chapters":
            result = handle_chapters(arguments)
        elif tool_name == "batch_search":
            result = handle_batch_search(arguments)
        elif tool_name == "text_to_speech":
            result = handle_text_to_speech(arguments)
        elif tool_name == "search_proximity":
            result = handle_search_proximity(arguments)
        elif tool_name == "identify_speakers":
            result = handle_identify_speakers(arguments)
        elif tool_name == "list_files":
            result = handle_list_files(arguments)
        elif tool_name == "list_cached":
            result = handle_list_cached(arguments)
        elif tool_name == "cache_stats":
            result = handle_cache_stats(arguments)
        elif tool_name == "clear_cache":
            result = handle_clear_cache(arguments)
        else:
            send_error(id, -32602, f"Unknown tool: {tool_name}")
            return

        send_response({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        })

    except FileNotFoundError as e:
        send_error(id, -32602, str(e))
    except ValueError as e:
        send_error(id, -32602, str(e))
    except Exception as e:
        send_error(id, -32603, f"Error: {str(e)}")


def handle_download_audio(arguments: dict) -> dict:
    """Handle download_audio tool call."""
    import subprocess
    import shutil
    import os
    import re

    url = arguments.get("url")
    output_dir = arguments.get("output_dir", os.path.expanduser("~/Downloads"))

    if not url:
        raise ValueError("Missing required parameter: url")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check for yt-dlp
    if not shutil.which("yt-dlp"):
        raise RuntimeError("yt-dlp not found. Install with: brew install yt-dlp")

    # Check for aria2c (optional but recommended)
    has_aria2c = shutil.which("aria2c") is not None

    # Build command
    cmd = [
        "yt-dlp",
        "-f", "bestaudio",
        "--concurrent-fragments", "4",
        "--no-playlist",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "--print", "after_move:filepath",  # Print the final file path
    ]

    if has_aria2c:
        cmd.extend(["--downloader", "aria2c", "--downloader-args", "aria2c:-x 16 -s 16 -k 1M"])

    cmd.append(url)

    # Run download
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or "Download failed"
        raise RuntimeError(f"Download failed: {error_msg}")

    # Extract the output file path from stdout
    output_lines = result.stdout.strip().split('\n')
    output_file = output_lines[-1] if output_lines else None

    # Get file info if available
    file_info = {}
    if output_file and os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        file_info = {
            "path": output_file,
            "filename": os.path.basename(output_file),
            "size_mb": round(file_size / (1024 * 1024), 2)
        }

    return {
        "success": True,
        "url": url,
        "output_dir": output_dir,
        "file": file_info,
        "aria2c_used": has_aria2c,
        "message": f"Audio downloaded to {output_file}" if output_file else "Download complete"
    }


def handle_search_audio(arguments: dict) -> dict:
    """Handle search_audio tool call."""
    audio_path = arguments.get("audio_path")
    keywords = arguments.get("keywords", [])
    model_size = arguments.get("model_size", "tiny")
    include_full = arguments.get("include_full_text", False)

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")
    if not keywords:
        raise ValueError("Missing required parameter: keywords")

    if include_full:
        result = search_audio_full(
            audio_path, keywords,
            model_size=model_size
        )
    else:
        result = search_audio(
            audio_path, keywords,
            model_size=model_size
        )

    result["model_used"] = model_size
    return result


def handle_transcribe_audio(arguments: dict) -> dict:
    """Handle transcribe_audio tool call."""
    audio_path = arguments.get("audio_path")
    model_size = arguments.get("model_size", "tiny")

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")

    result = transcribe_audio(audio_path, model_size)

    return {
        "text": result["text"],
        "language": result["language"],
        "duration": result["duration"],
        "duration_formatted": f"{int(result['duration'] // 60)}:{int(result['duration'] % 60):02d}",
        "segment_count": len(result.get("segments", [])),
        "cached": result.get("cached", False),
        "model_used": model_size
    }


def handle_search_proximity(arguments: dict) -> dict:
    """Handle search_proximity tool call."""
    audio_path = arguments.get("audio_path")
    keyword1 = arguments.get("keyword1")
    keyword2 = arguments.get("keyword2")
    max_distance = arguments.get("max_distance", 30)
    model_size = arguments.get("model_size", "tiny")

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")
    if not keyword1:
        raise ValueError("Missing required parameter: keyword1")
    if not keyword2:
        raise ValueError("Missing required parameter: keyword2")

    matches = search_audio_proximity(
        audio_path, keyword1, keyword2,
        max_distance=max_distance,
        model_size=model_size
    )

    return {
        "query": f"'{keyword1}' within {max_distance} words of '{keyword2}'",
        "match_count": len(matches),
        "matches": matches,
        "model_used": model_size
    }


def handle_batch_search(arguments: dict) -> dict:
    """Handle batch_search tool call."""
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    audio_paths = arguments.get("audio_paths", [])
    keywords = arguments.get("keywords", [])
    model_size = arguments.get("model_size", "tiny")
    workers = arguments.get("workers", 2)

    if not audio_paths:
        raise ValueError("Missing required parameter: audio_paths")
    if not keywords:
        raise ValueError("Missing required parameter: keywords")

    # Validate all paths exist
    valid_paths = []
    errors = []
    for path in audio_paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            errors.append({"path": path, "error": "File not found"})

    results = {}

    def process_file(path):
        try:
            return path, search_audio(path, keywords, model_size=model_size)
        except Exception as e:
            return path, {"error": str(e)}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, p): p for p in valid_paths}
        for future in as_completed(futures):
            path, result = future.result()
            results[path] = result

    # Aggregate stats
    total_matches = 0
    for path, file_results in results.items():
        if "error" not in file_results:
            for kw, matches in file_results.items():
                total_matches += len(matches)

    return {
        "files_processed": len(valid_paths),
        "files_with_errors": len(errors),
        "total_matches": total_matches,
        "results": results,
        "errors": errors if errors else None,
        "model_used": model_size
    }


def handle_list_files(arguments: dict) -> dict:
    """Handle list_files tool call."""
    import os
    import glob as glob_module

    DEFAULT_PATTERNS = ["*.mp3", "*.m4a", "*.wav", "*.webm", "*.mp4", "*.mkv", "*.ogg", "*.flac"]

    directory = arguments.get("directory")
    pattern = arguments.get("pattern")
    recursive = arguments.get("recursive", False)

    if not directory:
        raise ValueError("Missing required parameter: directory")

    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    # Build search pattern(s)
    files = []
    if pattern:
        patterns = [pattern]
    else:
        patterns = DEFAULT_PATTERNS

    for p in patterns:
        if recursive:
            search_pattern = os.path.join(directory, "**", p)
            files.extend(glob_module.glob(search_pattern, recursive=True))
        else:
            search_pattern = os.path.join(directory, p)
            files.extend(glob_module.glob(search_pattern))

    # Deduplicate and sort
    files = sorted(set(files))

    # Get file info
    audio_files = []
    for f in files:
        try:
            size = os.path.getsize(f)
            audio_files.append({
                "path": f,
                "name": os.path.basename(f),
                "size_mb": round(size / (1024 * 1024), 2)
            })
        except OSError:
            pass

    return {
        "directory": directory,
        "pattern": pattern,
        "recursive": recursive,
        "count": len(audio_files),
        "files": audio_files
    }


def handle_cache_stats(arguments: dict) -> dict:
    """Handle cache_stats tool call."""
    return get_cache_stats()


def handle_clear_cache(arguments: dict) -> dict:
    """Handle clear_cache tool call."""
    count = clear_cache()
    return {
        "cleared": count,
        "message": f"Cleared {count} cached transcriptions"
    }


def handle_list_cached(arguments: dict) -> dict:
    """Handle list_cached tool call."""
    entries = list_cached()
    return {
        "count": len(entries),
        "transcriptions": entries,
        "message": f"Found {len(entries)} cached transcription(s)"
    }


def _get_style_instruction(style: str, read_aloud: bool = False, output_dir: str = "~/Desktop", safe_title: str = "") -> str:
    """Return formatting instructions for a given note style."""

    base_prefix = (
        "IMPORTANT: You MUST now rewrite the file at txt_path using the Write tool. "
        "Do NOT leave the raw transcription as-is. Do NOT create .md files. "
        "For any follow-up tool calls (chapters, search, deep_search, etc.), use the audio_path field from this response — do NOT guess the filename. "
    )
    base_suffix = (
        "\n\nWrite the final notes to txt_path using the Write tool. "
        "After writing, respond ONLY with: Done. Notes saved to ~/Desktop/<filename>"
    )

    if read_aloud:
        import os as _os, shutil as _shutil
        _obsidian_installed = (
            _os.path.exists("/Applications/Obsidian.app")
            or bool(_shutil.which("obsidian"))
        )
        audio_filename = f"{safe_title}.mp3" if safe_title else "notes_audio.mp3"
        if _obsidian_installed:
            embed_instruction = (
                f"After TTS completes, re-open txt_path and add ![[{audio_filename}]] on the very first line "
                f"(before the title), then add `> Press Cmd+E before playing — prevents audio from pausing on scroll` "
                "on the line after the embed. Save again. "
            )
        else:
            embed_instruction = ""
        base_suffix = (
            "\n\nWrite the final notes to txt_path using the Write tool. "
            "THEN: Take the notes you just wrote — SKIP the title, source URL, duration, date, and any metadata lines at the top. Start from the first real content section heading. Take that content and "
            "strip the markdown formatting (remove #, **, -, >, ![], ---, callout syntax, links) "
            "so it reads as plain text. Keep every word and all the information exactly as written — "
            "do NOT rewrite or summarize, just clean the formatting so TTS can read it naturally. "
            "Section headers become spoken section titles. "
            "Run the text_to_speech tool with that spoken script, "
            f'output_dir="{output_dir}", output_filename="{audio_filename}". '
            + embed_instruction +
            "After everything, respond ONLY with: Done. Notes saved to ~/Desktop/<filename>"
        )

    styles = {
        "tldr": (
            "Create the shortest possible summary. Must fit on one screen.\n"
            "\n"
            "FORMAT:\n"
            "- Title as a top header\n"
            "- Source URL | Duration | Date on one line\n"
            "- ---\n"
            "- One 2-3 sentence overview paragraph\n"
            "- 5-8 bullet points max, each one line\n"
            "- **Bold** the single most important term or name in each bullet\n"
            "- No sections, no headers, no callouts, no quotes — just clean bullets\n"
            "- End with one bold takeaway line\n"
        ),
        "notes": (
            "Create clean, structured notes with clear hierarchy.\n"
            "\n"
            "FORMAT:\n"
            "- Title as a top header\n"
            "- Metadata block: Source URL, Duration, Date\n"
            "- ---\n"
            "- 3-6 section headers based on the main topics\n"
            "- Nested bullet points under each section (2 levels max)\n"
            "- **Bold** key terms and names throughout\n"
            "- Short paragraphs only — never more than 3 lines\n"
            "- One > blockquote if there's a standout quote worth preserving\n"
            "- Keep it scannable — someone should grasp the content in 60 seconds\n"
        ),
        "highlight": (
            "Create formatted notes with visual emphasis on key insights.\n"
            "\n"
            "FORMAT:\n"
            "- Title as a top header\n"
            "- Metadata block: Source URL, Duration, Date\n"
            "- ---\n"
            "- Section headers for each major topic\n"
            "- Nested bullet points with **bold key terms**\n"
            "- Use > [!tip] callout blocks for the 2-4 most important insights\n"
            "- Use > [!info] callout blocks for definitions or context\n"
            "- Use > blockquotes with timestamps for 2-3 key direct quotes\n"
            "- Use **bold** and *italic* generously for emphasis\n"
            "- Add a --- separator between major sections\n"
            "- End with a Key Takeaways section using a > [!summary] callout\n"
        ),
        "eye-candy": (
            "Create the most visually rich, beautifully formatted notes possible. "
            "Every section should be a visual experience — the reader should absorb "
            "the content by scanning, not reading.\n"
            "\n"
            "FORMAT:\n"
            "- Title as a top header\n"
            "- Metadata block: Source URL, Duration, Date\n"
            "- ---\n"
            "- Section headers for every topic shift\n"
            "- Nested bullet points (up to 3 levels) with **bold** and *italic*\n"
            "- > [!tip] callout blocks for key insights (use liberally, 4-6 throughout)\n"
            "- > [!info] callout blocks for context, background, definitions\n"
            "- > [!warning] callout blocks for common mistakes or misconceptions\n"
            "- > [!example] callout blocks for concrete examples mentioned\n"
            "- > blockquotes with timestamps for 3-5 standout direct quotes\n"
            "- Tables anywhere a comparison or list of items is discussed\n"
            "- --- separators between major sections\n"
            "- Checklists (- [ ]) for any action items or recommendations\n"
            "- End with:\n"
            "  1. A > [!summary] Key Takeaways callout with numbered list\n"
            "  2. A table of Related Topics / Further Reading if applicable\n"
            "\n"
            "The goal: someone opens this file in Obsidian and says 'wow'.\n"
        ),
        "quiz": (
            "Generate a multiple-choice quiz from the content. Do NOT write notes.\n"
            "\n"
            "FORMAT:\n"
            "- Title as a top header with 'Quiz' appended\n"
            "- Metadata block: Source URL, Duration, Date\n"
            "- ---\n"
            "- 10-15 multiple-choice questions\n"
            "- Each question:\n"
            "  - Numbered (1, 2, 3...)\n"
            "  - The question in **bold**\n"
            "  - Four options labeled A) B) C) D)\n"
            "  - One blank line between questions\n"
            "- ---\n"
            "- Answer Key section at the bottom\n"
            "  - Format: 1. B | 2. A | 3. D (compact, one line per 5 answers)\n"
            "  - Brief explanation for each answer on the next line\n"
            "\n"
            "Questions should test real understanding, not trivial details.\n"
        ),
    }

    body = styles.get(style, styles["notes"])
    return base_prefix + body + base_suffix


def handle_take_notes(arguments: dict) -> dict:
    """Handle take_notes tool call - download, transcribe, save .txt to Desktop."""
    import os
    import re

    url = arguments.get("url")
    output_dir = arguments.get("output_dir", os.path.expanduser("~/Desktop"))
    model_size = arguments.get("model_size", "tiny")
    style = arguments.get("style", "notes")
    read_aloud = arguments.get("read_aloud", False)

    if not url:
        raise ValueError("Missing required parameter: url")

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Download audio to ~/Downloads
    download_result = handle_download_audio({"url": url})

    if not download_result.get("success"):
        raise RuntimeError("Download failed: " + download_result.get("message", "unknown error"))

    file_info = download_result.get("file", {})
    if not file_info.get("path"):
        raise RuntimeError("Download succeeded but output file not found")
    audio_path = file_info["path"]
    title = os.path.splitext(file_info["filename"])[0]

    # Step 2: Transcribe
    result = transcribe_audio(audio_path, model_size)
    text = result["text"]
    duration = result["duration"]

    # Step 3: Save raw transcription as .txt on Desktop
    # Clean title for filename (remove special chars)
    safe_title = re.sub(r'[^\w\s\-]', '', title)
    safe_title = re.sub(r'\s+', ' ', safe_title).strip()
    if not safe_title:
        safe_title = "notes"
    txt_filename = f"{safe_title}.txt"
    txt_path = os.path.join(output_dir, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {url}\n")
        f.write(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}\n")
        f.write(f"Title: {title}\n")
        f.write("=" * 60 + "\n\n")
        f.write(text)

    # Style-specific formatting instructions
    instruction = _get_style_instruction(style, read_aloud=read_aloud, output_dir=output_dir, safe_title=safe_title)

    return {
        "success": True,
        "txt_path": txt_path,
        "audio_path": audio_path,
        "title": title,
        "duration": duration,
        "duration_formatted": f"{int(duration // 60)}:{int(duration % 60):02d}",
        "language": result["language"],
        "cached": result.get("cached", False),
        "model_used": model_size,
        "style": style,
        "transcription": text,
        "instruction": instruction,
    }


def handle_identify_speakers(arguments: dict) -> dict:
    """Handle identify_speakers tool call."""
    try:
        from .speakers import identify_speakers
    except ImportError:
        raise RuntimeError(
            "Missing dependencies: simple-diarizer. "
            "Install with: pip install simple-diarizer"
        )

    audio_path = arguments.get("audio_path")
    model_size = arguments.get("model_size", "tiny")
    num_speakers = arguments.get("num_speakers")

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")

    result = identify_speakers(
        audio_path,
        model_size=model_size,
        num_speakers=num_speakers,
    )

    return {
        "speakers": result["speakers"],
        "segment_count": len(result["segments"]),
        "segments": result["segments"],
        "duration": result["duration"],
        "duration_formatted": result["duration_formatted"],
        "language": result["language"],
        "cached": result.get("cached", False),
        "model_used": model_size,
    }


def handle_deep_search(arguments: dict) -> dict:
    """Handle deep_search tool call."""
    try:
        from .embeddings import deep_search
    except ImportError:
        raise RuntimeError(
            "Missing dependencies: sentence-transformers. "
            "Install with: pip install sentence-transformers"
        )

    audio_path = arguments.get("audio_path")
    query = arguments.get("query")
    model_size = arguments.get("model_size", "tiny")
    top_k = arguments.get("top_k", 5)

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")
    if not query:
        raise ValueError("Missing required parameter: query")

    return deep_search(
        audio_path,
        query,
        model_size=model_size,
        top_k=top_k,
    )


def handle_chapters(arguments: dict) -> dict:
    """Handle chapters tool call."""
    try:
        from .embeddings import detect_chapters
    except ImportError:
        raise RuntimeError(
            "Missing dependencies: sentence-transformers. "
            "Install with: pip install sentence-transformers"
        )

    audio_path = arguments.get("audio_path")
    model_size = arguments.get("model_size", "tiny")
    sensitivity = arguments.get("sensitivity", 0.4)

    if not audio_path:
        raise ValueError("Missing required parameter: audio_path")

    return detect_chapters(
        audio_path,
        model_size=model_size,
        sensitivity=sensitivity,
    )


def handle_text_to_speech(arguments: dict) -> dict:
    """Handle text_to_speech tool call."""
    try:
        from .tts import text_to_speech, read_aloud
    except ImportError:
        raise RuntimeError(
            "Missing dependencies: kokoro. "
            "Install with: pip install kokoro soundfile"
        )

    text = arguments.get("text")
    file_path = arguments.get("file_path")
    voice = arguments.get("voice", "af_heart")
    output_dir = arguments.get("output_dir", "~/Desktop")
    output_filename = arguments.get("output_filename")
    speed = arguments.get("speed", 1.0)

    if file_path:
        return read_aloud(file_path, voice=voice, speed=speed)

    if not text:
        raise ValueError("Either text or file_path is required")

    return text_to_speech(
        text,
        voice=voice,
        output_dir=output_dir,
        output_filename=output_filename,
        speed=speed,
    )


def handle_request(request: dict) -> None:
    """Route JSON-RPC request to appropriate handler."""
    method = request.get("method")
    id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        handle_initialize(id, params)
    elif method == "notifications/initialized":
        pass  # No response needed for notifications
    elif method == "tools/list":
        handle_tools_list(id)
    elif method == "tools/call":
        handle_tools_call(id, params)
    else:
        if id is not None:
            send_error(id, -32601, f"Method not found: {method}")


def main() -> None:
    """Main MCP server loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            handle_request(request)
        except json.JSONDecodeError:
            send_error(None, -32700, "Parse error")
        except Exception as e:
            send_error(None, -32603, f"Internal error: {str(e)}")


if __name__ == "__main__":
    main()
