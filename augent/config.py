"""
Augent configuration — loads user defaults from ~/.augent/config.yaml

Users can set defaults for model_size, output directories, clip padding, etc.
Per-call arguments always override config values.
"""

import os

_CONFIG_PATH = os.path.expanduser("~/.augent/config.yaml")
_JSON_CONFIG_PATH = os.path.expanduser("~/.augent/config.json")

DEFAULTS = {
    "model_size": "tiny",
    "output_dir": "~/Downloads",
    "notes_output_dir": "~/Desktop",
    "clip_padding": 15,
    "context_words": 25,
    "tts_voice": "af_heart",
    "tts_speed": 1.0,
    "disabled_tools": [],
}

_config = None


def get_config() -> dict:
    """Load config from ~/.augent/config.yaml (or .json fallback).

    Returns merged dict: user values override DEFAULTS.
    Unknown keys are silently ignored.
    Missing file = all defaults.
    """
    global _config
    if _config is not None:
        return _config

    _config = dict(DEFAULTS)

    user = _load_yaml() or _load_json() or {}

    # Only accept known keys
    for key in DEFAULTS:
        if key in user:
            _config[key] = user[key]

    return _config


def get(key: str):
    """Get a single config value."""
    return get_config()[key]


def _load_yaml() -> dict | None:
    """Try loading YAML config. Returns None if file missing or PyYAML not installed."""
    try:
        import yaml
    except ImportError:
        return None

    try:
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return None


def _load_json() -> dict | None:
    """Fallback: try loading JSON config."""
    import json

    try:
        with open(_JSON_CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
