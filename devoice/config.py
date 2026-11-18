"""Application-wide constants and configuration for Devoice."""

from __future__ import annotations

from typing import Any

from devoice import __version__

# ── Application identity ────────────────────────────────────────────────────
APP_NAME: str = "Devoice"
APP_VERSION: str = __version__

# ── Supported input audio formats ───────────────────────────────────────────
SUPPORTED_INPUT_FORMATS: list[str] = [
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".opus",
    ".webm",
]

# ── Output format definitions ───────────────────────────────────────────────
# Each key is a human-readable display name shown in the UI.
# Values carry the file extension, optional bitrate (for lossy codecs),
# and optional bit depth (for lossless codecs).
OUTPUT_FORMATS: dict[str, dict[str, Any]] = {
    "WAV (16-bit)": {
        "ext": ".wav",
        "bitrate": None,
        "bit_depth": 16,
    },
    "WAV (24-bit)": {
        "ext": ".wav",
        "bitrate": None,
        "bit_depth": 24,
    },
    "WAV (32-bit float)": {
        "ext": ".wav",
        "bitrate": None,
        "bit_depth": 32,
    },
    "FLAC (16-bit)": {
        "ext": ".flac",
        "bitrate": None,
        "bit_depth": 16,
    },
    "FLAC (24-bit)": {
        "ext": ".flac",
        "bitrate": None,
        "bit_depth": 24,
    },
    "MP3 (128 kbps)": {
        "ext": ".mp3",
        "bitrate": "128k",
        "bit_depth": None,
    },
    "MP3 (192 kbps)": {
        "ext": ".mp3",
        "bitrate": "192k",
        "bit_depth": None,
    },
    "MP3 (320 kbps)": {
        "ext": ".mp3",
        "bitrate": "320k",
        "bit_depth": None,
    },
    "OGG Vorbis (192 kbps)": {
        "ext": ".ogg",
        "bitrate": "192k",
        "bit_depth": None,
    },
}

# ── Default output location ────────────────────────────────────────────────
DEFAULT_OUTPUT_SUBDIR: str = "devoice_output"
