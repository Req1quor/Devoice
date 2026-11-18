"""Unit tests for the SeparationEngine device detection and basic properties."""

import pytest
import torch
from devoice.engine import SeparationEngine
from devoice.model_manager import ModelManager


def test_model_manager_registry():
    """Verify default models are properly registered in ModelManager."""
    models = ModelManager.list_models()
    assert "bs_roformer" in models
    assert "mdx_net" in models
    info = ModelManager.get_model("bs_roformer")
    assert info.name == "bs_roformer"
    assert info.arch == "roformer"


def test_is_cuda_available():
    """Verify is_cuda_available returns boolean matching torch."""
    assert SeparationEngine.is_cuda_available() == torch.cuda.is_available()
