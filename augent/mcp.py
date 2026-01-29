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
else:
    from .core import (
        search_audio,
        search_audio_full,
        transcribe_audio,
        search_audio_proximity,
        get_cache_stats,
        clear_cache
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
