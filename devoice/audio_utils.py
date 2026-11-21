"""Audio utility functions — post-processing, acoustic analysis, format conversion, and inspection."""

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


@dataclass
class AudioDiagnostic:
    """Acoustic profile and dynamic treatment recommendations for a given track."""

    path: Path
    filename: str
    peak_dbfs: float
    rms_dbfs: float
    sub_bass_ratio: float
    high_freq_ratio: float
    sample_rate: int
    duration_seconds: float
    channels: int

    # Dynamic recommendations & clear justifications
    recommend_true_peak: bool
    true_peak_reason: str

    recommend_subbass: bool
    subbass_reason: str

    recommend_debleed: bool
    debleed_reason: str

    @property
    def duration_display(self) -> str:
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def summary_headline(self) -> str:
        ch_str = "Stéréo" if self.channels >= 2 else "Mono"
        return f"{self.filename} · {self.duration_display} · {self.sample_rate // 1000}kHz {ch_str} · Pic: {self.peak_dbfs:.1f} dBFS"


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


# ── Intelligent Acoustic Analysis ──────────────────────────────────────────


def analyze_audio_track(path: Path | str) -> AudioDiagnostic:
    """Perform fast, intelligent acoustic analysis to recommend tailored post-processing.

    Inspects peak levels, dynamic range, sub-bass rumble (<65Hz), and high-frequency
    energy (>8kHz) to adapt treatments specifically to the dropped audio.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier audio introuvable : {path}")

    # Read audio with soundfile or torchaudio/ffmpeg fallback
    try:
        data, sr = sf.read(str(path), dtype="float32")
    except Exception:
        try:
            import torchaudio as ta

            wav, sr = ta.load(str(path))
            data = wav.numpy().T
        except Exception as exc:
            raise RuntimeError(f"Impossible d'analyser le fichier {path.name}: {exc}") from exc

    if data.ndim > 1:
        mono = np.mean(data, axis=1)
        channels = data.shape[1]
    else:
        mono = data
        channels = 1

    total_samples = len(mono)
    duration_s = total_samples / max(1, sr)

    # 1. Peak & RMS analysis
    peak = float(np.max(np.abs(mono))) if total_samples > 0 else 0.0
    peak_dbfs = 20.0 * math.log10(peak) if peak > 1e-6 else -100.0

    rms = float(np.sqrt(np.mean(mono**2))) if total_samples > 0 else 0.0
    rms_dbfs = 20.0 * math.log10(rms) if rms > 1e-6 else -100.0

    # 2. Spectral Analysis (sample slices across intro, middle, outro for speed)
    if total_samples > sr * 10:
        idx1 = int(total_samples * 0.2)
        idx2 = int(total_samples * 0.5)
        idx3 = int(total_samples * 0.8)
        chunk_len = int(sr * 2.5)
        sample_slice = np.concatenate(
            [
                mono[idx1 : idx1 + chunk_len],
                mono[idx2 : idx2 + chunk_len],
                mono[idx3 : idx3 + chunk_len],
            ]
        )
    else:
        sample_slice = mono

    slice_len = len(sample_slice)
    if slice_len > 0:
        fft_vals = np.abs(np.fft.rfft(sample_slice))
        freqs = np.fft.rfftfreq(slice_len, 1.0 / sr)
        total_energy = float(np.sum(fft_vals**2)) + 1e-9

        sub_energy = float(np.sum(fft_vals[freqs < 65.0] ** 2))
        high_energy = float(np.sum(fft_vals[freqs > 8000.0] ** 2))

        sub_ratio = sub_energy / total_energy
        high_ratio = high_energy / total_energy
    else:
        sub_ratio = 0.0
        high_ratio = 0.0

    # ── Tailored Recommendation Logic ───────────────────────────────────

    # Rule 1: True Peak Normalization (-1.0 dBFS)
    # If peak is close to digital ceiling (>= -0.8 dBFS), inter-sample distortion is likely in DAWs
    if peak_dbfs >= -0.8:
        rec_tp = True
        tp_reason = f"Pic à {peak_dbfs:.1f} dBFS · Risque de saturation inter-échantillon"
    else:
        rec_tp = False
        tp_reason = f"Marge saine ({peak_dbfs:.1f} dBFS) · Non nécessaire"

    # Rule 2: Sub-Bass Filter (65 Hz)
    # If sub-bass (<65Hz) energy is high (>4.5%), low-end rumble will dirty the acapella
    if sub_ratio >= 0.045:
        rec_sub = True
        sub_reason = f"Infrabasses/rumble détectés ({sub_ratio*100:.1f}%) · Nettoyage recommandé"
    else:
        rec_sub = False
        sub_reason = f"Basses propres ({sub_ratio*100:.1f}%) · Inactif pour préserver la chaleur"

    # Rule 3: Spectral De-bleed
    # If cymbals/high percussion energy is dense (>8.0%), bleed risk is significant
    if high_ratio >= 0.08:
        rec_debleed = True
        debleed_reason = f"Aigus denses ({high_ratio*100:.1f}%) · Risque de fuite charleys/cymbales"
    else:
        rec_debleed = False
        debleed_reason = f"Spectre équilibré ({high_ratio*100:.1f}%) · Inactif pour préserver le timbre"

    return AudioDiagnostic(
        path=path,
        filename=path.name,
        peak_dbfs=peak_dbfs,
        rms_dbfs=rms_dbfs,
        sub_bass_ratio=sub_ratio,
        high_freq_ratio=high_ratio,
        sample_rate=sr,
        duration_seconds=duration_s,
        channels=channels,
        recommend_true_peak=rec_tp,
        true_peak_reason=tp_reason,
        recommend_subbass=rec_sub,
        subbass_reason=sub_reason,
        recommend_debleed=rec_debleed,
        debleed_reason=debleed_reason,
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
        return path

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

    min_len = min(len(v_data), len(i_data))
    v = v_data[:min_len]
    instru = i_data[:min_len]

    frame_size = 2048
    hop_size = 512
    num_frames = (min_len - frame_size) // hop_size

    if num_frames <= 0:
        return

    v_out = np.copy(v)
    attenuation_factor = math.pow(10.0, -abs(reduction_db) / 20.0)

    for i in range(0, min_len - frame_size, hop_size):
        v_frame = v[i : i + frame_size]
        i_frame = instru[i : i + frame_size]

        v_energy = np.mean(v_frame**2)
        i_energy = np.mean(i_frame**2)

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
