"""
Augent CLI - Command line interface for audio keyword search

Features:
- Single file and batch processing
- Multiple output formats (JSON, CSV, SRT, VTT, Markdown)
- Clip extraction
- Proximity search
- Live progress output
- Cache management
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .core import (
    search_audio,
    search_audio_full,
    transcribe_audio,
    transcribe_audio_streaming,
    search_audio_proximity,
    get_cache_stats,
    clear_cache,
    clear_model_cache,
    TranscriptionProgress
)
from .search import find_keyword_matches
from .export import export_matches, export_transcription
from .clips import export_clips


def print_progress(progress: TranscriptionProgress, quiet: bool = False):
    """Print progress update to stderr."""
    if quiet:
        return

    if progress.status == "loading_model":
        print(f"\r{progress.message}", end="", file=sys.stderr)
    elif progress.status == "transcribing":
        print(f"\r{progress.message}", end="", file=sys.stderr)
    elif progress.status == "segment":
        print(f"\n  {progress.message}", file=sys.stderr)
    elif progress.status == "complete":
        print(f"\n{progress.message}", file=sys.stderr)


def process_single_file(
    audio_path: str,
    keywords: List[str],
    args: argparse.Namespace
) -> dict:
    """Process a single audio file."""
    if args.full:
        result = search_audio_full(
            audio_path,
            keywords,
            model_size=args.model,
            use_cache=not args.no_cache
        )
    else:
        result = search_audio(
            audio_path,
            keywords,
            model_size=args.model,
            use_cache=not args.no_cache
        )

    return result


def process_batch(
    audio_paths: List[str],
    keywords: List[str],
    args: argparse.Namespace
) -> dict:
    """Process multiple audio files."""
    results = {}

    if args.workers > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_path = {
                executor.submit(process_single_file, path, keywords, args): path
                for path in audio_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                    if not args.quiet:
                        print(f"Completed: {path}", file=sys.stderr)
                except Exception as e:
                    results[path] = {"error": str(e)}
                    if not args.quiet:
                        print(f"Error processing {path}: {e}", file=sys.stderr)
    else:
        # Sequential processing
        for path in audio_paths:
            if not args.quiet:
                print(f"\nProcessing: {path}", file=sys.stderr)
            try:
                results[path] = process_single_file(path, keywords, args)
            except Exception as e:
                results[path] = {"error": str(e)}
                if not args.quiet:
                    print(f"Error: {e}", file=sys.stderr)

    return results


def cmd_search(args: argparse.Namespace):
    """Handle search command."""
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("Error: No keywords provided", file=sys.stderr)
        sys.exit(1)

    # Expand glob patterns for batch processing
    audio_paths = []
    for pattern in args.audio:
        expanded = glob.glob(pattern)
        if expanded:
            audio_paths.extend(expanded)
        elif os.path.exists(pattern):
            audio_paths.append(pattern)
        else:
            print(f"Warning: No files match '{pattern}'", file=sys.stderr)

    if not audio_paths:
        print("Error: No audio files found", file=sys.stderr)
        sys.exit(1)

    # Process info
    if not args.quiet:
        print(f"Audio files: {len(audio_paths)}", file=sys.stderr)
        print(f"Keywords: {keywords}", file=sys.stderr)
        print(f"Model: {args.model}", file=sys.stderr)
        print("", file=sys.stderr)

    # Process
    if len(audio_paths) == 1:
        # Single file - use streaming for live progress
        audio_path = audio_paths[0]

        if args.stream and not args.quiet:
            # Stream progress
            transcription = None
            for progress in transcribe_audio_streaming(
                audio_path,
                args.model,
                use_cache=not args.no_cache
            ):
                print_progress(progress, args.quiet)

            # Now search
            transcription = transcribe_audio(
                audio_path, args.model, use_cache=True
            )
            matches = find_keyword_matches(
                transcription["words"],
                keywords
            )

            # Group results
            if args.full:
                result = {
                    "text": transcription["text"],
                    "language": transcription["language"],
                    "duration": transcription["duration"],
                    "matches": matches
                }
            else:
                result = {}
                for match in matches:
                    kw = match["keyword"]
                    if kw not in result:
                        result[kw] = []
                    result[kw].append({
                        "timestamp": match["timestamp"],
                        "timestamp_seconds": match["timestamp_seconds"],
                        "snippet": match["snippet"]
                    })
        else:
            result = process_single_file(audio_path, keywords, args)
            matches = []
            if args.full:
                matches = result.get("matches", [])
            else:
                for kw, kw_matches in result.items():
                    for m in kw_matches:
                        m["keyword"] = kw
                        matches.append(m)
    else:
        # Batch processing
        result = process_batch(audio_paths, keywords, args)
        matches = []  # Flat list for exports

        # Flatten matches from all files
        for path, file_result in result.items():
            if "error" not in file_result:
                if args.full:
                    for m in file_result.get("matches", []):
                        m["file"] = path
                        matches.append(m)
                else:
                    for kw, kw_matches in file_result.items():
                        for m in kw_matches:
                            m["keyword"] = kw
                            m["file"] = path
                            matches.append(m)

    # Export clips if requested
    if args.export_clips and matches:
        if not args.quiet:
            print(f"\nExporting clips to: {args.export_clips}", file=sys.stderr)

        audio_for_clips = audio_paths[0] if len(audio_paths) == 1 else None
        if audio_for_clips:
            clips = export_clips(
                audio_for_clips,
                matches,
                args.export_clips,
                padding=args.clip_padding
            )
            if not args.quiet:
                print(f"Exported {len(clips)} clips", file=sys.stderr)

    # Output
    if args.format == "json":
        output = json.dumps(result, indent=2)
    elif args.format in ("csv", "srt", "vtt", "markdown", "md"):
        output = export_matches(matches, args.format)
    else:
        output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if not args.quiet:
            print(f"\nResults written to: {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_transcribe(args: argparse.Namespace):
    """Handle transcribe command (full transcription only)."""
    if not os.path.exists(args.audio):
        print(f"Error: File not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Transcribing: {args.audio}", file=sys.stderr)
        print(f"Model: {args.model}", file=sys.stderr)

    # Stream transcription
    if args.stream and not args.quiet:
        for progress in transcribe_audio_streaming(
            args.audio,
            args.model,
            use_cache=not args.no_cache
        ):
            print_progress(progress, args.quiet)

    transcription = transcribe_audio(
        args.audio,
        args.model,
        use_cache=True
    )

    # Format output
    if args.format in ("srt", "vtt"):
        output = export_transcription(
            transcription["segments"],
            args.format
        )
    else:
        output = json.dumps({
            "text": transcription["text"],
            "language": transcription["language"],
            "duration": transcription["duration"],
            "segments": transcription["segments"]
        }, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if not args.quiet:
            print(f"\nTranscription written to: {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_proximity(args: argparse.Namespace):
    """Handle proximity search command."""
    if not os.path.exists(args.audio):
        print(f"Error: File not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Searching: {args.audio}", file=sys.stderr)
        print(f"Finding '{args.keyword1}' near '{args.keyword2}' (within {args.distance} words)", file=sys.stderr)

    matches = search_audio_proximity(
        args.audio,
        args.keyword1,
        args.keyword2,
        max_distance=args.distance,
        model_size=args.model,
        use_cache=not args.no_cache
    )

    # Output
    if args.format == "json":
        output = json.dumps(matches, indent=2)
    else:
        output = export_matches(matches, args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if not args.quiet:
            print(f"\nResults written to: {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_cache(args: argparse.Namespace):
    """Handle cache management command."""
    if args.cache_action == "stats":
        stats = get_cache_stats()
        print(json.dumps(stats, indent=2))
    elif args.cache_action == "clear":
        count = clear_cache()
        print(f"Cleared {count} cached transcriptions")
    elif args.cache_action == "clear-models":
        clear_model_cache()
        print("Cleared model cache")


def cmd_help(args: argparse.Namespace):
    """Show detailed help and quick start guide."""
    help_text = """
================================================================================
                         AUGENT - Audio Intelligence Tool
================================================================================

QUICK START
-----------
1. Clone & Install:
   git clone https://github.com/AugentDevs/Augent.git
   cd Augent
   pip install -e .[web]

2. Run Web UI:
   python3 -m augent.web

3. Open browser:
   http://127.0.0.1:8888

COMMANDS
--------
  augent search <audio> "<keywords>"    Search audio for keywords
  augent transcribe <audio>             Full transcription
  augent proximity <audio> "A" "B"      Find keyword A near keyword B
  augent cache stats                    View cache statistics
  augent cache clear                    Clear transcription cache
  augent help                           Show this help

WEB UI
------
  python3 -m augent.web                 Start web interface on port 8888
  python3 -m augent.web --port 9000     Use custom port
  python3 -m augent.web --share         Create public Gradio link

MCP SERVER (for Claude Code)
----------------------------
  python3 -m augent.mcp                 Start MCP server for Claude integration

EXAMPLES
--------
  # Search for keywords in audio
  augent search podcast.mp3 "startup,funding,growth"

  # Use better model for accuracy
  augent search audio.mp3 "keyword" --model small

  # Batch process multiple files
  augent search "*.mp3" "keyword" --workers 4

  # Export results to CSV/SRT
  augent search audio.mp3 "keyword" --format csv --output results.csv
  augent search audio.mp3 "keyword" --format srt --output matches.srt

  # Extract audio clips around keyword matches
  augent search audio.mp3 "important" --export-clips ./clips
  augent search audio.mp3 "keyword" --export-clips ./clips --clip-padding 10

  # Find two keywords within 30 words of each other
  augent proximity audio.mp3 "problem" "solution" --distance 30
  # Example: finds "we had a problem... here's the solution" if within 30 words

  # Full transcription with subtitles
  augent transcribe audio.mp3 --format srt --output subtitles.srt

MODEL SIZES
-----------
  tiny   - Fastest, great accuracy (DEFAULT - use for most tasks)
  base   - Fast, excellent accuracy
  small  - Medium speed, superior accuracy
  medium - Slow, outstanding accuracy
  large  - Slowest, maximum accuracy (lyrics, accents, poor audio)

REQUIREMENTS
------------
  - Python 3.9+
  - FFmpeg (for audio processing)
  - pip install -e .[web] for Web UI
  - pip install -e .[all] for all features

MORE INFO
---------
  GitHub: https://github.com/AugentDevs/Augent

================================================================================
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        description="Augent - Local audio keyword search using Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  augent search audio.mp3 "money,success,growth"

  # Search with larger model for better accuracy
  augent search podcast.mp3 "startup" --model small

  # Batch processing
  augent search "podcasts/*.mp3" "keyword" --workers 4

  # Export to different formats
  augent search audio.mp3 "keyword" --format csv --output results.csv
  augent search audio.mp3 "keyword" --format srt --output matches.srt

  # Extract audio clips around matches
  augent search audio.mp3 "keyword" --export-clips ./clips --clip-padding 5

  # Proximity search - find keywords within N words of each other
  augent proximity audio.mp3 "startup" "funding" --distance 30  # within 30 words

  # Full transcription
  augent transcribe audio.mp3 --format srt --output subtitles.srt

  # Cache management
  augent cache stats
  augent cache clear

Model sizes:
  tiny   - Fastest, incredibly accurate, use for nearly everything (default)
  base   - Fast, excellent accuracy
  small  - Medium speed, superior accuracy
  medium - Slow, outstanding accuracy
  large  - Slowest, maximum accuracy (e.g., finding lyrics in unknown songs)
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search audio for keywords")
    search_parser.add_argument(
        "audio",
        nargs="+",
        help="Audio file(s) or glob pattern (e.g., '*.mp3')"
    )
    search_parser.add_argument(
        "keywords",
        help="Comma-separated keywords to search for"
    )
    search_parser.add_argument(
        "--model", "-m",
        default="tiny",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: tiny)"
    )
    search_parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Include full transcription in output"
    )
    search_parser.add_argument(
        "--format",
        default="json",
        choices=["json", "csv", "srt", "vtt", "markdown", "md"],
        help="Output format (default: json)"
    )
    search_parser.add_argument(
        "--output", "-o",
        help="Write output to file"
    )
    search_parser.add_argument(
        "--export-clips",
        metavar="DIR",
        help="Export audio clips around matches to directory"
    )
    search_parser.add_argument(
        "--clip-padding",
        type=float,
        default=5.0,
        help="Seconds of audio before/after each clip (default: 5)"
    )
    search_parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Parallel workers for batch processing (default: 1)"
    )
    search_parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="Stream transcription progress to stderr"
    )
    search_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable transcription caching"
    )
    search_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    # Transcribe command
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio without keyword search"
    )
    transcribe_parser.add_argument("audio", help="Audio file to transcribe")
    transcribe_parser.add_argument(
        "--model", "-m",
        default="tiny",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: tiny)"
    )
    transcribe_parser.add_argument(
        "--format",
        default="json",
        choices=["json", "srt", "vtt"],
        help="Output format (default: json)"
    )
    transcribe_parser.add_argument("--output", "-o", help="Write output to file")
    transcribe_parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="Stream transcription progress"
    )
    transcribe_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching"
    )
    transcribe_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    # Proximity command
    proximity_parser = subparsers.add_parser(
        "proximity",
        help="Find keyword1 near keyword2"
    )
    proximity_parser.add_argument("audio", help="Audio file to search")
    proximity_parser.add_argument("keyword1", help="Primary keyword")
    proximity_parser.add_argument("keyword2", help="Must appear nearby")
    proximity_parser.add_argument(
        "--distance", "-d",
        type=int,
        default=30,
        help="Max words allowed between keyword1 and keyword2 (default: 30)"
    )
    proximity_parser.add_argument(
        "--model", "-m",
        default="tiny",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: tiny)"
    )
    proximity_parser.add_argument(
        "--format",
        default="json",
        choices=["json", "csv", "markdown"],
        help="Output format (default: json)"
    )
    proximity_parser.add_argument("--output", "-o", help="Write output to file")
    proximity_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching"
    )
    proximity_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage transcription cache")
    cache_parser.add_argument(
        "cache_action",
        choices=["stats", "clear", "clear-models"],
        help="Cache action"
    )

    # Help command
    help_parser = subparsers.add_parser("help", help="Show detailed help and quick start guide")

    # Parse and dispatch
    args = parser.parse_args()

    if args.command is None:
        # Default to search if positional args provided (backwards compatibility)
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "search":
            cmd_search(args)
        elif args.command == "transcribe":
            cmd_transcribe(args)
        elif args.command == "proximity":
            cmd_proximity(args)
        elif args.command == "cache":
            cmd_cache(args)
        elif args.command == "help":
            cmd_help(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
