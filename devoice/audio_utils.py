"""Audio utility functions — format conversion, normalisation, and inspection."""

from __future__ import annotations

import logging
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


# ── Audio info ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AudioInfo:
    """Lightweight container for audio file metadata."""

    path: Path
    sample_rate: int
    channels: int
    frames: int
    duration_seconds: float
    format: str
    subtype: str

    @property
    def duration_display(self) -> str:
        """Return duration formatted as ``MM:SS``."""
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"


def get_audio_info(path: Path | str) -> AudioInfo:
    """Read metadata from *path* without loading the full audio data.

    Parameters
    ----------
    path:
        Path to an audio file readable by *soundfile*.

    Returns
    -------
    AudioInfo
        Populated metadata object.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    RuntimeError
        If *soundfile* cannot read the file.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        info = sf.info(str(path))
    except Exception as exc:
        raise RuntimeError(f"Cannot read audio info from {path}: {exc}") from exc

    return AudioInfo(
        path=path,
        sample_rate=info.samplerate,
        channels=info.channels,
        frames=info.frames,
        duration_seconds=info.duration,
        format=info.format,
        subtype=info.subtype,
    )


# ── Format conversion ──────────────────────────────────────────────────────


def _find_ffmpeg() -> str:
    """Locate the ``ffmpeg`` binary or raise."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise FileNotFoundError(
            "ffmpeg not found on PATH. Install ffmpeg to enable audio "
            "format conversion."
        )
    return ffmpeg


def convert_audio(
    input_path: Path | str,
    output_path: Path | str,
    *,
    bitrate: Optional[str] = None,
    bit_depth: Optional[int] = None,
    sample_rate: Optional[int] = None,
) -> Path:
    """Convert *input_path* to *output_path* using ffmpeg.

    Parameters
    ----------
    input_path:
        Source audio file.
    output_path:
        Destination file.  The extension determines the target codec.
    bitrate:
        Target bitrate string for lossy codecs (e.g. ``"320k"``).
    bit_depth:
        Bit depth for lossless codecs (16, 24, or 32).
    sample_rate:
        Target sample rate in Hz.  ``None`` → keep original.

    Returns
    -------
    Path
        The resolved *output_path*.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist or ffmpeg is missing.
    RuntimeError
        If the ffmpeg process exits with an error.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    ffmpeg = _find_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [ffmpeg, "-y", "-i", str(input_path)]

    # Codec mapping based on output extension
    ext = output_path.suffix.lower()
    codec_map: dict[str, str] = {
        ".mp3": "libmp3lame",
        ".ogg": "libvorbis",
        ".flac": "flac",
        ".wav": "pcm_s16le",  # overridden below if bit_depth is set
        ".m4a": "aac",
        ".aac": "aac",
        ".opus": "libopus",
    }

    codec = codec_map.get(ext)
    if codec:
        # Adjust PCM codec for the requested bit depth
        if ext == ".wav" and bit_depth is not None:
            pcm_map = {16: "pcm_s16le", 24: "pcm_s24le", 32: "pcm_f32le"}
            codec = pcm_map.get(bit_depth, codec)
        cmd.extend(["-acodec", codec])

    if bitrate is not None:
        cmd.extend(["-b:a", bitrate])

    if sample_rate is not None:
        cmd.extend(["-ar", str(sample_rate)])

    # FLAC bit depth via sample format
    if ext == ".flac" and bit_depth is not None:
        fmt_map = {16: "s16", 24: "s32"}  # FLAC only supports s16/s32
        sample_fmt = fmt_map.get(bit_depth)
        if sample_fmt:
            cmd.extend(["-sample_fmt", sample_fmt])

    cmd.append(str(output_path))

    logger.info("Running ffmpeg: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg conversion failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}"
        )

    logger.info("Converted %s → %s", input_path, output_path)
    return output_path


# ── Normalisation ───────────────────────────────────────────────────────────


def normalize_audio(
    audio: np.ndarray,
    *,
    target_peak: float = 0.95,
) -> np.ndarray:
    """Peak-normalise *audio* so its absolute maximum equals *target_peak*.

    Parameters
    ----------
    audio:
        Audio array of shape ``(channels, samples)`` or ``(samples,)``.
    target_peak:
        Desired peak amplitude in ``(0.0, 1.0]``.

    Returns
    -------
    numpy.ndarray
        Normalised copy of *audio* with the same shape and dtype.

    Raises
    ------
    ValueError
        If *target_peak* is out of range or *audio* is silent.
    """
    if not 0.0 < target_peak <= 1.0:
        raise ValueError(
            f"target_peak must be in (0.0, 1.0], got {target_peak}"
        )

    current_peak: float = float(np.max(np.abs(audio)))

    if current_peak == 0.0:
        raise ValueError("Cannot normalise silent audio (peak is 0).")

    gain = target_peak / current_peak
    normalised = audio * gain

    logger.debug(
        "Normalised audio: peak %.4f → %.4f (gain %.4f)",
        current_peak,
        target_peak,
        gain,
    )
    return normalised
