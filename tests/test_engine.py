"""Unit tests for the SeparationEngine device detection and basic properties."""

import pytest
import torch
from devoice.engine import SeparationEngine
from devoice.model_manager import ModelManager


def test_model_manager_registry():
    """Verify default models are properly registered in ModelManager."""
    models = ModelManager.list_models()
    assert "htdemucs" in models
    assert "htdemucs_ft" in models
    info = ModelManager.get_model("htdemucs")
    assert info.name == "htdemucs"


def test_detect_device():
    """Verify that _detect_device returns 'cuda' or 'cpu'."""
    device = SeparationEngine._detect_device()
    assert device in ("cuda", "cpu")
    if torch.cuda.is_available():
        assert device == "cuda"
    else:
        assert device == "cpu"


def test_is_cuda_available():
    """Verify is_cuda_available returns boolean matching torch."""
    assert SeparationEngine.is_cuda_available() == torch.cuda.is_available()
