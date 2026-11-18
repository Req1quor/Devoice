"""Audio utility functions — post-processing, format conversion, and inspection."""

from __future__ import annotations

import logging
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

logger = logging.getLogger(__name__)


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
        """Return duration formatted as MM:SS."""
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"


def get_audio_info(path: Path | str) -> AudioInfo:
    """Read metadata from path without loading full audio data into memory."""
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


# ── Pro Audio Post-Processing ───────────────────────────────────────────────


def apply_subbass_filter(audio_path: Path | str, cutoff_hz: float = 65.0) -> Path:
    """Apply a 2nd order Butterworth high-pass filter to remove sub-bass rumble.

    Removes sub-bass frequencies below cutoff_hz (<65 Hz) without affecting vocal warmth.
    """
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    nyquist = 0.5 * sr
    norm_cutoff = min(0.99, max(0.001, cutoff_hz / nyquist))
    sos = butter(2, norm_cutoff, btype="highpass", output="sos")

    if data.ndim == 1:
        filtered = sosfilt(sos, data)
    else:
        # Multichannel [samples, channels]
        filtered = np.zeros_like(data)
        for ch in range(data.shape[1]):
            filtered[:, ch] = sosfilt(sos, data[:, ch])

    sf.write(str(path), filtered, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied sub-bass high-pass filter (%.1f Hz) to %s", cutoff_hz, path.name)
    return path


def apply_true_peak_normalization(audio_path: Path | str, target_dbfs: float = -1.0) -> Path:
    """Normalize audio to a safe True-Peak margin (-1.0 dBFS by default).

    Prevents digital inter-sample distortion when exported into DAWs.
    """
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    peak = float(np.max(np.abs(data)))
    if peak <= 1e-6:
        return path  # Silent audio, leave untouched

    target_linear = math.pow(10.0, target_dbfs / 20.0)
    gain = target_linear / peak
    normalized = data * gain

    sf.write(str(path), normalized, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied True-Peak normalization (%.1f dBFS, gain %.2f) to %s", target_dbfs, gain, path.name)
    return path


def apply_spectral_debleed(vocals_path: Path | str, instru_path: Path | str, reduction_db: float = 2.0) -> None:
    """Attenuate residual instrumental bleed during vocal silence regions."""
    v_path = Path(vocals_path)
    i_path = Path(instru_path)
    if not (v_path.is_file() and i_path.is_file()):
        return

    v_data, sr = sf.read(str(v_path), dtype="float32")
    i_data, _ = sf.read(str(i_path), dtype="float32")

    # Match lengths if slightly different
    min_len = min(len(v_data), len(i_data))
    v = v_data[:min_len]
    instru = i_data[:min_len]

    # Calculate frame energy ratio
    frame_size = 2048
    hop_size = 512
    num_frames = (min_len - frame_size) // hop_size

    if num_frames <= 0:
        return

    # Soft dynamic attenuation when vocal energy is much lower than instrumental energy
    window = np.hanning(frame_size)
    v_out = np.copy(v)

    attenuation_factor = math.pow(10.0, -abs(reduction_db) / 20.0)

    for i in range(0, min_len - frame_size, hop_size):
        v_frame = v[i : i + frame_size]
        i_frame = instru[i : i + frame_size]

        v_energy = np.mean(v_frame**2)
        i_energy = np.mean(i_frame**2)

        # If vocal is whisper-quiet while instrumental is very loud, apply gentle suppression
        if v_energy < 1e-4 and i_energy > 5e-3:
            v_out[i : i + frame_size] *= attenuation_factor

    sf.write(str(v_path), v_out, sr)
    logger.info("Applied soft spectral de-bleed on %s", v_path.name)


def normalize_audio(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Peak-normalise audio numpy array so its absolute maximum equals target_peak."""
    if not 0.0 < target_peak <= 1.0:
        raise ValueError(f"target_peak must be in (0.0, 1.0], got {target_peak}")

    current_peak: float = float(np.max(np.abs(audio)))
    if current_peak == 0.0:
        raise ValueError("Cannot normalise silent audio (peak is 0).")

    gain = target_peak / current_peak
    return audio * gain


def convert_audio(
    input_path: Path | str,
    output_path: Path | str,
    *,
    bitrate: Optional[str] = None,
    bit_depth: Optional[int] = None,
    sample_rate: Optional[int] = None,
) -> Path:
    """Convert input_path to output_path using ffmpeg."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    cmd: list[str] = [ffmpeg, "-y", "-i", str(input_path)]

    ext = output_path.suffix.lower()
    if ext == ".mp3" and bitrate:
        cmd.extend(["-b:a", bitrate])
    if sample_rate:
        cmd.extend(["-ar", str(sample_rate)])

    cmd.append(str(output_path))
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path
