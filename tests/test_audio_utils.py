"""Unit tests for audio utilities (info, normalisation, pro filters, acoustic diagnostic)."""

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
from devoice.audio_utils import (
    AudioDiagnostic,
    AudioInfo,
    analyze_audio_track,
    apply_subbass_filter,
    apply_true_peak_normalization,
    get_audio_info,
    normalize_audio,
)


def test_get_audio_info(sample_audio_path: Path):
    """Verify get_audio_info reads metadata correctly."""
    info = get_audio_info(sample_audio_path)
    assert isinstance(info, AudioInfo)
    assert info.sample_rate == 44100
    assert info.channels == 2
    assert abs(info.duration_seconds - 1.0) < 0.05
    assert info.duration_display == "00:01"


def test_normalize_audio():
    """Verify normalize_audio scales peaks appropriately."""
    signal = np.array([0.1, -0.5, 0.3], dtype=np.float32)
    normalised = normalize_audio(signal, target_peak=0.95)
    assert np.isclose(np.max(np.abs(normalised)), 0.95)


def test_normalize_audio_silent():
    """Verify normalizing silent audio raises ValueError."""
    silent = np.zeros(100, dtype=np.float32)
    with pytest.raises(ValueError, match="silent audio"):
        normalize_audio(silent)


def test_apply_subbass_filter(tmp_path: Path):
    """Verify subbass filter preserves valid audio and attenuates sub-bass."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # 30 Hz sub-bass rumble + 440 Hz vocal tone
    signal = 0.5 * np.sin(2 * np.pi * 30 * t) + 0.5 * np.sin(2 * np.pi * 440 * t)
    wav_path = tmp_path / "subbass_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_subbass_filter(wav_path, cutoff_hz=65.0)
    assert res.exists()
    filtered_data, _ = sf.read(str(res))
    assert len(filtered_data) == sr


def test_apply_true_peak_normalization(tmp_path: Path):
    """Verify true peak normalization scales audio to target dBFS."""
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = 0.2 * np.sin(2 * np.pi * 1000 * t)  # peak is 0.2
    wav_path = tmp_path / "peak_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_true_peak_normalization(wav_path, target_dbfs=-1.0)
    norm_data, _ = sf.read(str(res))
    expected_peak = 10.0 ** (-1.0 / 20.0)
    assert np.isclose(np.max(np.abs(norm_data)), expected_peak, atol=0.01)


def test_analyze_audio_track(tmp_path: Path):
    """Verify analyze_audio_track accurately diagnoses peak and frequency content."""
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    # Hot peak (0.99 = -0.08 dBFS) with high sub-bass (30 Hz)
    signal = 0.99 * np.sin(2 * np.pi * 30 * t)
    wav_path = tmp_path / "hot_sub.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    diag = analyze_audio_track(wav_path)
    assert isinstance(diag, AudioDiagnostic)
    assert diag.peak_dbfs > -0.5
    assert diag.recommend_true_peak is True
    assert diag.recommend_subbass is True
    assert "Pic" in diag.true_peak_reason
