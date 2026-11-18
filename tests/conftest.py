"""Pytest configuration and fixtures for Devoice test suite."""

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary output directory."""
    out_dir = tmp_path / "devoice_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@pytest.fixture
def sample_audio_path(tmp_path: Path) -> Path:
    """Generate a valid 1-second stereo sine wave WAV file for testing."""
    sample_rate = 44100
    duration_s = 1.0
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    
    # 440 Hz tone (stereo)
    tone = 0.2 * np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack((tone, tone)).astype(np.float32)

    wav_path = tmp_path / "test_sample.wav"
    sf.write(str(wav_path), stereo_signal, sample_rate, subtype="PCM_16")
    return wav_path
