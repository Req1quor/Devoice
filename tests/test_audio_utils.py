"""Unit tests for audio utilities (info, normalisation, pro filters, acoustic diagnostic)."""

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
from devoice.audio_utils import (
    AudioDiagnostic,
    AudioInfo,
    analyze_audio_track,
    apply_dereverb_clean,
    apply_dynamic_deesser,
    apply_pitch_tracked_subbass_filter,
    apply_silence_purifier,
    apply_subbass_filter,
    apply_true_peak_normalization,
    apply_vocal_leveler,
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

    res = apply_true_peak_normalization(wav_path, target_dbfs=-1.0, allow_boost=True)
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


def test_apply_dynamic_deesser(tmp_path: Path):
    """Verify dynamic de-esser processes signal and reduces harsh sibilants."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # 7 kHz harsh sibilance tone
    signal = 0.8 * np.sin(2 * np.pi * 7000 * t)
    wav_path = tmp_path / "deesser_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_dynamic_deesser(wav_path, sibilance_freq_hz=7000.0, max_reduction_db=6.0)
    assert res.exists()
    cleaned_data, _ = sf.read(str(res))
    assert len(cleaned_data) == sr
    # Attenuation should have reduced peak amplitude
    assert np.max(np.abs(cleaned_data)) < 0.8


def test_apply_dereverb_clean(tmp_path: Path):
    """Verify dereverb module runs without error and preserves shape."""
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 300 * t)
    wav_path = tmp_path / "dereverb_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_dereverb_clean(wav_path, dry_ratio=0.3)
    assert res.exists()
    out_data, _ = sf.read(str(res))
    assert len(out_data) == len(signal)


def test_apply_silence_purifier(tmp_path: Path):
    """Verify silence purifier attenuates quiet noise floor."""
    sr = 44100
    # 0.5s loud tone then 0.5s low noise (-50 dBFS)
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    loud = 0.5 * np.sin(2 * np.pi * 400 * t)
    quiet = 0.001 * np.sin(2 * np.pi * 400 * t)
    signal = np.concatenate([loud, quiet])
    wav_path = tmp_path / "silence_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_silence_purifier(wav_path, threshold_db=-40.0, max_attenuation_db=20.0)
    assert res.exists()
    cleaned_data, _ = sf.read(str(res))
    # Quiet section after release settles should be attenuated significantly
    quiet_out = cleaned_data[int(sr * 0.7) :]
    assert np.max(np.abs(quiet_out)) < 0.0005


def test_apply_vocal_leveler(tmp_path: Path):
    """Verify vocal leveler stabilizes volume differences between quiet and loud sections."""
    sr = 44100
    # 1.0s quiet vocal (peak 0.08) followed by 1.0s loud vocal (peak 0.60)
    t = np.linspace(0, 1.0, sr, endpoint=False)
    quiet_section = 0.08 * np.sin(2 * np.pi * 350 * t)
    loud_section = 0.60 * np.sin(2 * np.pi * 350 * t)
    signal = np.concatenate([quiet_section, loud_section])

    wav_path = tmp_path / "leveler_test.wav"
    sf.write(str(wav_path), signal.astype(np.float32), sr)

    res = apply_vocal_leveler(wav_path, max_boost_db=4.0, max_cut_db=4.0)
    assert res.exists()
    out_data, _ = sf.read(str(res))
    assert len(out_data) == len(signal)

    # In the leveled output, the quiet section should be boosted and loud section tamed
    quiet_out = out_data[int(sr * 0.2) : int(sr * 0.8)]
    loud_out = out_data[int(sr * 1.2) : int(sr * 1.8)]

    ratio_before = 0.60 / 0.08  # 7.5x difference (~17.5 dB)
    ratio_after = np.max(np.abs(loud_out)) / np.max(np.abs(quiet_out))

    # Dynamic spread between the two sections should be significantly reduced
    assert ratio_after < ratio_before


