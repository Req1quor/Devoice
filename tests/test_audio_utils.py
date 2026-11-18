"""Unit tests for audio utilities (info, normalisation)."""

import numpy as np
import pytest
from pathlib import Path
from devoice.audio_utils import get_audio_info, normalize_audio, AudioInfo


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
