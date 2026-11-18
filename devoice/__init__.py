"""Devoice — State-of-the-art vocal & instrumental source separation."""

__version__ = "2.0.0"

# Automatically ensure portable FFmpeg is on PATH before any audio library is loaded
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass
