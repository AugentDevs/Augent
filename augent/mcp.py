"""
Augent MCP Server

Model Context Protocol server for Claude Desktop and Claude Code integration.
Exposes Augent as a native tool that Claude can call directly.

Tools exposed:
- download_audio: Download audio from video URLs (YouTube, etc.) at maximum speed
- search_audio: Search for keywords in audio files
- transcribe_audio: Full transcription without keyword search
- search_proximity: Find keywords appearing near each other
- batch_search: Search multiple audio files in parallel
- list_audio_files: List audio files in a directory
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
import signal
import time
import uuid
from typing import Any

# Track active live Twitter Space recordings
_active_recordings: dict = {}

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
                    "name": "list_audio_files",
                    "description": "List audio files in a directory matching a pattern. Useful for discovering files before batch processing.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory path to search"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern for matching files. Default: *.mp3"
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
                {
                    "name": "list_cached",
                    "description": "List all cached transcriptions with their titles, durations, dates, and file paths to markdown files. Useful for browsing what has already been transcribed.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "augent_spaces",
                    "description": "Download a Twitter/X Space audio. Starts in the background and returns instantly with a recording_id. Use augent_spaces_check to check progress, augent_spaces_stop to cancel.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Twitter/X Space URL (e.g., https://x.com/i/spaces/1yNxaNvaMYQKj)"
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
                    "name": "augent_spaces_check",
                    "description": "Check the status of a Twitter Space download started by augent_spaces. Returns whether it's still downloading, complete, or errored, plus file details.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "recording_id": {
                                "type": "string",
                                "description": "The recording ID returned by augent_spaces"
                            }
                        },
                        "required": ["recording_id"]
                    }
                },
                {
                    "name": "augent_spaces_stop",
                    "description": "Stop a live Twitter Space recording. Kills the download process and saves whatever has been captured so far.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "recording_id": {
                                "type": "string",
                                "description": "The recording ID returned by augent_spaces"
                            }
                        },
                        "required": ["recording_id"]
                    }
                }
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
        elif tool_name == "search_audio":
            result = handle_search_audio(arguments)
        elif tool_name == "transcribe_audio":
            result = handle_transcribe_audio(arguments)
        elif tool_name == "search_proximity":
            result = handle_search_proximity(arguments)
        elif tool_name == "batch_search":
            result = handle_batch_search(arguments)
        elif tool_name == "list_audio_files":
            result = handle_list_audio_files(arguments)
        elif tool_name == "cache_stats":
            result = handle_cache_stats(arguments)
        elif tool_name == "clear_cache":
            result = handle_clear_cache(arguments)
        elif tool_name == "list_cached":
            result = handle_list_cached(arguments)
        elif tool_name == "augent_spaces":
            result = handle_augent_spaces(arguments)
        elif tool_name == "augent_spaces_check":
            result = handle_augent_spaces_check(arguments)
        elif tool_name == "augent_spaces_stop":
            result = handle_augent_spaces_stop(arguments)

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


def _normalize_twitter_space_url(url: str) -> str:
    """Normalize Twitter/X Space URLs for compatibility."""
    url = url.replace("https://x.com/", "https://twitter.com/")
    # Strip /peek suffix if present
    if url.endswith("/peek"):
        url = url[:-5]
    return url


def handle_download_audio(arguments: dict) -> dict:
    """Handle download_audio tool call."""
    import subprocess
    import os
    import re

    url = arguments.get("url")
    output_dir = arguments.get("output_dir", os.path.expanduser("~/Downloads"))

    if not url:
        raise ValueError("Missing required parameter: url")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check for yt-dlp
    if not subprocess.run(["which", "yt-dlp"], capture_output=True).returncode == 0:
        raise RuntimeError("yt-dlp not found. Install with: brew install yt-dlp")

    # Check for aria2c (optional but recommended)
    has_aria2c = subprocess.run(["which", "aria2c"], capture_output=True).returncode == 0

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


def handle_list_audio_files(arguments: dict) -> dict:
    """Handle list_audio_files tool call."""
    import os
    import glob as glob_module

    directory = arguments.get("directory")
    pattern = arguments.get("pattern", "*.mp3")
    recursive = arguments.get("recursive", False)

    if not directory:
        raise ValueError("Missing required parameter: directory")

    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    # Build search pattern
    if recursive:
        search_pattern = os.path.join(directory, "**", pattern)
        files = glob_module.glob(search_pattern, recursive=True)
    else:
        search_pattern = os.path.join(directory, pattern)
        files = glob_module.glob(search_pattern)

    # Get file info
    audio_files = []
    for f in sorted(files):
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


def _get_twitter_cookies_path() -> str:
    """Get path to Twitter cookies file, generating it from auth.json if needed."""
    import os

    augent_dir = os.path.expanduser("~/.augent")
    auth_path = os.path.join(augent_dir, "auth.json")
    cookies_path = os.path.join(augent_dir, "twitter_cookies.txt")

    # If auth.json exists, generate/refresh cookies.txt from it
    if os.path.exists(auth_path):
        auth_mtime = os.path.getmtime(auth_path)
        cookies_mtime = os.path.getmtime(cookies_path) if os.path.exists(cookies_path) else 0

        if auth_mtime > cookies_mtime:
            with open(auth_path) as f:
                auth = json.load(f)
            auth_token = auth.get("auth_token", "")
            ct0 = auth.get("ct0", "")
            # Netscape cookies.txt format
            lines = [
                "# Netscape HTTP Cookie File",
                f".twitter.com\tTRUE\t/\tTRUE\t0\tauth_token\t{auth_token}",
                f".twitter.com\tTRUE\t/\tTRUE\t0\tct0\t{ct0}",
            ]
            os.makedirs(augent_dir, exist_ok=True)
            with open(cookies_path, "w") as f:
                f.write("\n".join(lines) + "\n")

    if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 0:
        return cookies_path

    return None


_SETUP_INSTRUCTIONS = (
    "Twitter requires a one-time setup to download Spaces.\n\n"
    "Steps (30 seconds):\n"
    "1. Open Chrome > go to twitter.com (make sure you're logged in)\n"
    "2. Press F12 (or Cmd+Option+I) to open DevTools\n"
    "3. Click Application tab > Cookies > https://twitter.com\n"
    "4. Find auth_token — copy its Value\n"
    "5. Find ct0 — copy its Value\n"
    "6. Create the file ~/.augent/auth.json with:\n"
    '   {"auth_token": "PASTE_HERE", "ct0": "PASTE_HERE"}\n\n'
    "Your tokens are stored locally and only sent to Twitter's own servers to fetch audio. "
    "Augent never posts, DMs, follows, or modifies anything on your account. "
    "To revoke access anytime, simply log out of Twitter or delete ~/.augent/auth.json."
)


def handle_augent_spaces(arguments: dict) -> dict:
    """Handle augent_spaces tool call. Auto-detects live vs ended, starts in background."""
    import subprocess
    import os
    import glob as glob_module

    url = arguments.get("url")
    output_dir = arguments.get("output_dir", os.path.expanduser("~/Downloads"))

    if not url:
        raise ValueError("Missing required parameter: url")

    cookies_path = _get_twitter_cookies_path()
    if not cookies_path:
        raise FileNotFoundError(_SETUP_INSTRUCTIONS)

    os.makedirs(output_dir, exist_ok=True)
    url = _normalize_twitter_space_url(url)

    # Step 1: Extract metadata + stream URL via yt-dlp (fast, ~5s)
    meta_cmd = [
        "yt-dlp",
        "--cookies", cookies_path,
        "--add-header", "Referer:https://twitter.com/",
        "--no-playlist", "--dump-json",
        url
    ]
    meta_result = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=30)

    if meta_result.returncode != 0:
        error = meta_result.stderr.strip()
        raise RuntimeError(f"Failed to fetch space info: {error[:300]}")

    meta = json.loads(meta_result.stdout)
    title = meta.get("title", "twitter_space")
    is_live = meta.get("is_live", False)

    # Snapshot files before download starts
    before = set(glob_module.glob(os.path.join(output_dir, "*")))

    if is_live:
        # Live space: get m3u8 URL, record from NOW with ffmpeg
        stream_cmd = [
            "yt-dlp",
            "--cookies", cookies_path,
            "--add-header", "Referer:https://twitter.com/",
            "--no-playlist", "-g", "-f", "bestaudio",
            url
        ]
        stream_result = subprocess.run(stream_cmd, capture_output=True, text=True, timeout=15)
        if stream_result.returncode != 0:
            raise RuntimeError("Failed to get stream URL")

        m3u8_url = stream_result.stdout.strip()
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
        output_file = os.path.join(output_dir, f"{safe_title}.m4a")

        process = subprocess.Popen(
            ["ffmpeg", "-y", "-i", m3u8_url, "-c", "copy", output_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    else:
        # Ended space: full download with yt-dlp
        output_file = None
        process = subprocess.Popen(
            [
                "yt-dlp", "-f", "bestaudio",
                "--cookies", cookies_path,
                "--add-header", "Referer:https://twitter.com/",
                "--no-playlist",
                "-o", f"{output_dir}/%(title)s.%(ext)s",
                url
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    recording_id = uuid.uuid4().hex[:8]
    _active_recordings[recording_id] = {
        "process": process,
        "pid": process.pid,
        "url": url,
        "output_dir": output_dir,
        "start_time": time.time(),
        "before_files": before,
        "is_live": is_live,
        "title": title,
        "output_file": output_file if is_live else None,
    }

    mode_str = "Live recording from current moment" if is_live else "Downloading full recording"
    return {
        "success": True,
        "recording_id": recording_id,
        "mode": "live" if is_live else "recording",
        "title": title,
        "url": url,
        "output_dir": output_dir,
        "pid": process.pid,
        "message": f"{mode_str} (ID: {recording_id}). Use augent_spaces_check to check progress, augent_spaces_stop to stop."
    }


def handle_augent_spaces_check(arguments: dict) -> dict:
    """Handle augent_spaces_check tool call. Check download/recording status."""
    import os
    import glob as glob_module

    recording_id = arguments.get("recording_id")
    if not recording_id:
        raise ValueError("Missing required parameter: recording_id")

    if recording_id not in _active_recordings:
        raise ValueError(f"No active download found with ID: {recording_id}")

    rec = _active_recordings[recording_id]
    process = rec["process"]
    output_dir = rec["output_dir"]
    before = rec["before_files"]
    elapsed = time.time() - rec["start_time"]

    poll = process.poll()

    # Find output file — use known path for live, detect for recordings
    output_file = rec.get("output_file")
    if not output_file:
        after = set(glob_module.glob(os.path.join(output_dir, "*")))
        new_files = after - before
        output_file = max(new_files, key=os.path.getmtime) if new_files else None

    file_info = {}
    if output_file and os.path.exists(output_file):
        file_info = {
            "path": output_file,
            "filename": os.path.basename(output_file),
            "size_mb": round(os.path.getsize(output_file) / (1024 * 1024), 2)
        }

    if poll is None:
        # Still running
        return {
            "recording_id": recording_id,
            "status": "downloading",
            "elapsed_seconds": round(elapsed),
            "elapsed_formatted": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
            "file": file_info,
            "message": f"Still downloading ({int(elapsed // 60)}m {int(elapsed % 60)}s elapsed)"
        }

    # Process finished
    if poll == 0:
        # Success — clean up tracking
        del _active_recordings[recording_id]
        return {
            "recording_id": recording_id,
            "status": "complete",
            "elapsed_seconds": round(elapsed),
            "elapsed_formatted": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
            "file": file_info,
            "message": f"Download complete. Saved to {output_file}" if output_file else "Download complete"
        }

    # Failed
    stderr = process.stderr.read().decode() if process.stderr else ""
    del _active_recordings[recording_id]
    return {
        "recording_id": recording_id,
        "status": "error",
        "error": stderr.strip()[:500] or "Download failed",
        "message": "Download failed"
    }


def handle_augent_spaces_stop(arguments: dict) -> dict:
    """Handle augent_spaces_stop tool call. Kill a live recording."""
    import os
    import glob as glob_module

    recording_id = arguments.get("recording_id")
    if not recording_id:
        raise ValueError("Missing required parameter: recording_id")

    if recording_id not in _active_recordings:
        raise ValueError(f"No active download found with ID: {recording_id}")

    rec = _active_recordings[recording_id]
    process = rec["process"]
    output_dir = rec["output_dir"]
    before = rec["before_files"]

    # Graceful stop via SIGINT, then escalate
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=30)
        except Exception:
            process.terminate()
            try:
                process.wait(timeout=10)
            except Exception:
                process.kill()

    elapsed = time.time() - rec["start_time"]

    # Find output file — use known path for live, detect for recordings
    output_file = rec.get("output_file")
    if not output_file:
        after = set(glob_module.glob(os.path.join(output_dir, "*")))
        new_files = after - before
        output_file = max(new_files, key=os.path.getmtime) if new_files else None

    file_info = {}
    if output_file and os.path.exists(output_file):
        file_info = {
            "path": output_file,
            "filename": os.path.basename(output_file),
            "size_mb": round(os.path.getsize(output_file) / (1024 * 1024), 2)
        }

    del _active_recordings[recording_id]

    return {
        "success": True,
        "recording_id": recording_id,
        "status": "stopped",
        "elapsed_seconds": round(elapsed),
        "elapsed_formatted": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
        "file": file_info,
        "message": f"Stopped after {int(elapsed // 60)}m {int(elapsed % 60)}s. Saved to {output_file}" if output_file else "Stopped"
    }


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
