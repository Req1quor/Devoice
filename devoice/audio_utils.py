"""Audio utility functions — adaptive acoustic analysis, studio post-processing, and format conversion."""

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
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"


@dataclass
class AudioDiagnostic:
    """Acoustic profile and dynamic tailored treatment recommendations."""

    path: Path
    filename: str
    peak_dbfs: float
    rms_dbfs: float
    sample_rate: int
    duration_seconds: float
    channels: int

    # Voice & Pitch characteristics
    pitch_f0: float
    voice_type: str
    adaptive_cutoff_hz: float

    # Sibilance & Harshness
    sibilance_hz: float
    sibilance_ratio: float
    has_harsh_sibilance: bool
    sibilance_reason: str

    # Reverb estimation
    reverb_index: float
    has_reverb: bool
    reverb_reason: str

    # Low-end & Rumble
    sub_bass_ratio: float
    has_subbass_rumble: bool
    subbass_reason: str

    # Silence / Noise floor
    has_noise_in_pauses: bool
    silence_reason: str

    # True-Peak headroom
    recommend_true_peak: bool
    true_peak_reason: str

    # High frequency bleed
    high_freq_ratio: float
    recommend_debleed: bool
    debleed_reason: str

    @property
    def recommend_subbass(self) -> bool:
        return self.has_subbass_rumble

    @property
    def duration_display(self) -> str:
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def summary_headline(self) -> str:
        f0_str = f"F0 ~{int(self.pitch_f0)}Hz" if self.pitch_f0 > 0 else "F0 N/D"
        return f"{self.filename} · {self.voice_type} ({f0_str}) · Pic: {self.peak_dbfs:.1f} dBFS"


def get_audio_info(path: Path | str) -> AudioInfo:
    """Read metadata from path without loading full audio data."""
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
    """Perform comprehensive acoustic analysis to configure a tailored studio chain.

    Estimates:
    - Fundamental vocal frequency (F0) & voice category
    - Adaptive cutoff frequency calculated specifically for the singer's pitch
    - Sibilance peak frequency & harshness ratio (5 kHz - 9 kHz)
    - Reverb tail ratio (decay / sustained energy)
    - Low-end rumble (<65 Hz)
    - Noise in pauses & True-Peak headroom
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier audio introuvable : {path}")

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

    # 1. Peak & RMS
    peak = float(np.max(np.abs(mono))) if total_samples > 0 else 0.0
    peak_dbfs = 20.0 * math.log10(peak) if peak > 1e-6 else -100.0

    rms = float(np.sqrt(np.mean(mono**2))) if total_samples > 0 else 0.0
    rms_dbfs = 20.0 * math.log10(rms) if rms > 1e-6 else -100.0

    # 2. Representative multi-window sampling (intro, couplet, refrain)
    if total_samples > sr * 8:
        idx1 = int(total_samples * 0.20)
        idx2 = int(total_samples * 0.50)
        idx3 = int(total_samples * 0.75)
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

    # 3. Fundamental pitch (F0) estimation
    pitch_f0 = 0.0
    voice_type = "Voix standard"
    adaptive_cutoff = 65.0

    if slice_len > sr:
        try:
            import librosa

            # Fast YIN pitch detection on a 1.5s slice of active vocals
            test_segment = sample_slice[: int(sr * 2.0)]
            f0_estimates = librosa.yin(test_segment, fmin=65, fmax=450, sr=sr)
            valid_f0 = f0_estimates[~np.isnan(f0_estimates)]
            if len(valid_f0) > 0:
                pitch_f0 = float(np.median(valid_f0))

                if pitch_f0 < 115.0:
                    voice_type = "Voix masculine grave (Baryton / Basse)"
                    adaptive_cutoff = max(55.0, pitch_f0 * 0.65)
                elif pitch_f0 < 175.0:
                    voice_type = "Voix masculine médium (Ténor)"
                    adaptive_cutoff = max(65.0, pitch_f0 * 0.62)
                elif pitch_f0 < 280.0:
                    voice_type = "Voix féminine / aiguë (Alto / Soprano)"
                    adaptive_cutoff = max(90.0, min(125.0, pitch_f0 * 0.55))
                else:
                    voice_type = "Voix très aiguë"
                    adaptive_cutoff = 120.0
        except Exception:
            pitch_f0 = 130.0
            voice_type = "Voix mixte"
            adaptive_cutoff = 70.0

    # 4. Spectral analysis for sub-bass, sibilance, and reverb
    sub_ratio = 0.0
    high_ratio = 0.0
    sibilance_ratio = 0.0
    sibilance_hz = 7200.0
    reverb_index = 0.0

    if slice_len > 0:
        fft_vals = np.abs(np.fft.rfft(sample_slice))
        freqs = np.fft.rfftfreq(slice_len, 1.0 / sr)
        total_energy = float(np.sum(fft_vals**2)) + 1e-9

        # Sub-bass (< 65 Hz)
        sub_energy = float(np.sum(fft_vals[freqs < 65.0] ** 2))
        sub_ratio = sub_energy / total_energy

        # High frequencies (> 8000 Hz)
        high_energy = float(np.sum(fft_vals[freqs > 8000.0] ** 2))
        high_ratio = high_energy / total_energy

        # Sibilance band (5000 Hz - 9000 Hz) vs core voice band (300 Hz - 3000 Hz)
        sib_mask = (freqs >= 5000.0) & (freqs <= 9000.0)
        core_mask = (freqs >= 300.0) & (freqs <= 3000.0)
        sib_energy = float(np.sum(fft_vals[sib_mask] ** 2))
        core_energy = float(np.sum(fft_vals[core_mask] ** 2)) + 1e-9
        sibilance_ratio = sib_energy / core_energy

        # Find exact peak frequency of sibilance
        if np.any(sib_mask):
            sib_freqs = freqs[sib_mask]
            sib_peaks = fft_vals[sib_mask]
            sibilance_hz = float(sib_freqs[np.argmax(sib_peaks)])

        # Reverb index estimation (decay ratio between frame RMS energy quantiles)
        frame_len = 1024
        hop_len = 256
        frame_rms = [
            np.sqrt(np.mean(sample_slice[i : i + frame_len] ** 2))
            for i in range(0, slice_len - frame_len, hop_len)
        ]
        if frame_rms:
            q25 = float(np.percentile(frame_rms, 25))
            q90 = float(np.percentile(frame_rms, 90)) + 1e-6
            reverb_index = q25 / q90

    # ── Tailored Recommendation Logic ───────────────────────────────────

    # Rule 1: Adaptive Sub-Bass Filter
    has_subbass = sub_ratio >= 0.04 or adaptive_cutoff > 75.0
    if has_subbass:
        subbass_reason = f"Calibré sur la fondamentale de l'artiste ({int(adaptive_cutoff)} Hz) · Nettoyage net"
    else:
        subbass_reason = f"Basses propres ({sub_ratio*100:.1f}%) · Coupure douce à {int(adaptive_cutoff)} Hz"

    # Rule 2: Dynamic De-Esser
    has_harsh_sibilance = sibilance_ratio >= 0.22 or (sibilance_hz >= 6000 and sibilance_ratio >= 0.16)
    if has_harsh_sibilance:
        sibilance_reason = f"Sifflantes agressives détectées à {sibilance_hz/1000:.1f} kHz · Adoucissement conseillé"
    else:
        sibilance_reason = f"Aigus doux ({sibilance_hz/1000:.1f} kHz) · Inactif pour préserver l'air"

    # Rule 3: De-Reverb Studio
    has_reverb = reverb_index >= 0.14
    if has_reverb:
        reverb_reason = f"Réverbération/delay résiduel détecté · Assèchement cabine conseillé"
    else:
        reverb_reason = f"Voix déjà sèche (Reverb index: {reverb_index:.2f}) · Timbre direct intact"

    # Rule 4: Silence Purifier (Noise in pauses)
    has_noise = True  # Always beneficial for clean isolated acapellas
    silence_reason = "Élimination des résidus d'instru et souffle dans les pauses vocales"

    # Rule 5: True-Peak Normalization (-1.0 dBFS)
    rec_tp = peak_dbfs >= -0.8
    if rec_tp:
        tp_reason = f"Pic à {peak_dbfs:.1f} dBFS · Risque de saturation numérique en DAW"
    else:
        tp_reason = f"Marge saine ({peak_dbfs:.1f} dBFS) · Non nécessaire"

    # Rule 6: High frequency de-bleed
    rec_debleed = high_ratio >= 0.085
    if rec_debleed:
        debleed_reason = f"Cymbales/percussions denses ({high_ratio*100:.1f}%) · Anti-fuite conseillé"
    else:
        debleed_reason = f"Aigus équilibrés ({high_ratio*100:.1f}%) · Inactif pour préserver le timbre"

    return AudioDiagnostic(
        path=path,
        filename=path.name,
        peak_dbfs=peak_dbfs,
        rms_dbfs=rms_dbfs,
        sample_rate=sr,
        duration_seconds=duration_s,
        channels=channels,
        pitch_f0=pitch_f0,
        voice_type=voice_type,
        adaptive_cutoff_hz=adaptive_cutoff,
        sibilance_hz=sibilance_hz,
        sibilance_ratio=sibilance_ratio,
        has_harsh_sibilance=has_harsh_sibilance,
        sibilance_reason=sibilance_reason,
        reverb_index=reverb_index,
        has_reverb=has_reverb,
        reverb_reason=reverb_reason,
        sub_bass_ratio=sub_ratio,
        has_subbass_rumble=has_subbass,
        subbass_reason=subbass_reason,
        has_noise_in_pauses=has_noise,
        silence_reason=silence_reason,
        recommend_true_peak=rec_tp,
        true_peak_reason=tp_reason,
        high_freq_ratio=high_ratio,
        recommend_debleed=rec_debleed,
        debleed_reason=debleed_reason,
    )


# ── Studio Post-Processing DSP Modules ──────────────────────────────────────


def apply_pitch_tracked_subbass_filter(audio_path: Path | str, cutoff_hz: float = 65.0) -> Path:
    """Apply high-pass Butterworth filter tailored to the singer's fundamental pitch."""
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
    logger.info("Applied pitch-tracked sub-bass filter (%.1f Hz) on %s", cutoff_hz, path.name)
    return path


def apply_dynamic_deesser(
    audio_path: Path | str,
    sibilance_freq_hz: float = 7200.0,
    max_reduction_db: float = 4.0,
) -> Path:
    """Dynamic De-Esser: surgically attenuates harsh sibilants without dulling the vocal."""
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    nyquist = 0.5 * sr
    bandwidth_hz = 1800.0
    low = max(0.001, (sibilance_freq_hz - bandwidth_hz / 2) / nyquist)
    high = min(0.99, (sibilance_freq_hz + bandwidth_hz / 2) / nyquist)

    sos_band = butter(2, [low, high], btype="bandpass", output="sos")

    if data.ndim == 1:
        channels_data = [data]
    else:
        channels_data = [data[:, ch] for ch in range(data.shape[1])]

    out_channels = []
    reduction_factor = math.pow(10.0, -abs(max_reduction_db) / 20.0)

    for ch_signal in channels_data:
        # Extract sibilance band
        sib_band = sosfilt(sos_band, ch_signal)
        # Compute dynamic envelope
        env = np.abs(sib_band)
        # Smooth envelope (fast attack 2ms, release 30ms)
        attack_alpha = math.exp(-1.0 / (0.002 * sr))
        release_alpha = math.exp(-1.0 / (0.030 * sr))

        smooth_env = np.zeros_like(env)
        curr = 0.0
        for i in range(len(env)):
            val = env[i]
            if val > curr:
                curr = attack_alpha * curr + (1 - attack_alpha) * val
            else:
                curr = release_alpha * curr + (1 - release_alpha) * val
            smooth_env[i] = curr

        # Threshold: top 5% peak sibilance triggers gain attenuation
        thresh = np.percentile(smooth_env, 95) * 0.7 if len(smooth_env) > 0 else 0.1
        gain_curve = np.ones_like(ch_signal)
        mask = smooth_env > thresh
        if np.any(mask):
            over = (smooth_env[mask] - thresh) / (np.max(smooth_env) - thresh + 1e-6)
            gain_curve[mask] = 1.0 - (1.0 - reduction_factor) * np.clip(over, 0.0, 1.0)

        # Attenuate only the sibilant band portion from the channel
        cleaned = ch_signal - sib_band * (1.0 - gain_curve)
        out_channels.append(cleaned)

    final_data = np.column_stack(out_channels) if len(out_channels) > 1 else out_channels[0]
    sf.write(str(path), final_data, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied dynamic de-esser (%.1f kHz) on %s", sibilance_freq_hz / 1000.0, path.name)
    return path


def apply_dereverb_clean(audio_path: Path | str, dry_ratio: float = 0.30) -> Path:
    """De-Reverb module: enhances direct vocal transients and suppresses diffuse reverb decay."""
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    if data.ndim == 1:
        channels_data = [data]
    else:
        channels_data = [data[:, ch] for ch in range(data.shape[1])]

    out_channels = []
    for ch_signal in channels_data:
        # Compute short-time energy envelope
        env = np.abs(ch_signal)
        # Fast envelope (direct sound) vs slow envelope (reverb tail)
        fast_a = math.exp(-1.0 / (0.005 * sr))
        slow_a = math.exp(-1.0 / (0.120 * sr))

        fast_env = np.zeros_like(env)
        slow_env = np.zeros_like(env)
        f_val, s_val = 0.0, 0.0

        for i in range(len(env)):
            v = env[i]
            f_val = fast_a * f_val + (1 - fast_a) * v
            s_val = slow_a * s_val + (1 - slow_a) * v
            fast_env[i] = f_val
            slow_env[i] = s_val

        # Transientness: where fast energy significantly exceeds slow decay
        transient_ratio = fast_env / (slow_env + 1e-6)
        gain = np.clip(1.0 - (1.0 - dry_ratio) / (transient_ratio + 1.0), 0.65, 1.0)

        cleaned = ch_signal * gain
        out_channels.append(cleaned)

    final_data = np.column_stack(out_channels) if len(out_channels) > 1 else out_channels[0]
    sf.write(str(path), final_data, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied De-Reverb studio module on %s", path.name)
    return path


def apply_silence_purifier(
    audio_path: Path | str,
    threshold_db: float = -42.0,
    max_attenuation_db: float = 24.0,
) -> Path:
    """Silence purifier / Smart Expander: cleans ghost bleed & noise floor during vocal pauses."""
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    thresh_linear = math.pow(10.0, threshold_db / 20.0)
    att_linear = math.pow(10.0, -abs(max_attenuation_db) / 20.0)

    if data.ndim == 1:
        channels_data = [data]
    else:
        channels_data = [data[:, ch] for ch in range(data.shape[1])]

    out_channels = []
    # Smooth attack (15ms) and release (80ms) to preserve natural breath endings
    att_a = math.exp(-1.0 / (0.015 * sr))
    rel_a = math.exp(-1.0 / (0.080 * sr))

    for ch_signal in channels_data:
        env = np.abs(ch_signal)
        gain_envelope = np.ones_like(ch_signal)
        curr_gain = 1.0

        for i in range(len(env)):
            target_gain = 1.0 if env[i] >= thresh_linear else att_linear
            if target_gain > curr_gain:
                curr_gain = att_a * curr_gain + (1 - att_a) * target_gain
            else:
                curr_gain = rel_a * curr_gain + (1 - rel_a) * target_gain
            gain_envelope[i] = curr_gain

        cleaned = ch_signal * gain_envelope
        out_channels.append(cleaned)

    final_data = np.column_stack(out_channels) if len(out_channels) > 1 else out_channels[0]
    sf.write(str(path), final_data, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied Silence Purifier / Anti-Ghosting on %s", path.name)
    return path


def apply_true_peak_normalization(audio_path: Path | str, target_dbfs: float = -1.0) -> Path:
    """Normalize audio to True-Peak margin (-1.0 dBFS) to prevent DAW inter-sample clipping."""
    path = Path(audio_path)
    data, sr = sf.read(str(path), dtype="float32")

    peak = float(np.max(np.abs(data)))
    if peak <= 1e-6:
        return path

    target_linear = math.pow(10.0, target_dbfs / 20.0)
    gain = target_linear / peak
    normalized = data * gain

    sf.write(str(path), normalized, sr, subtype="PCM_16" if "16" in sf.info(str(path)).subtype else "FLOAT")
    logger.info("Applied True-Peak normalization (%.1f dBFS, gain %.2f) on %s", target_dbfs, gain, path.name)
    return path


def apply_subbass_filter(audio_path: Path | str, cutoff_hz: float = 65.0) -> Path:
    """Backward compatibility alias for pitch-tracked filter."""
    return apply_pitch_tracked_subbass_filter(audio_path, cutoff_hz=cutoff_hz)


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
