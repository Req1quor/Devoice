"""Devoice — State-of-the-art vocal & instrumental source separation."""

__version__ = "2.0.0"

try:
    from devoice.runtime_manager import ensure_ffmpeg_paths

    ensure_ffmpeg_paths()
except Exception:
    pass
