"""Model registry and metadata for UVR5 / RoFormer / MDX-Net models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelInfo:
    """Immutable descriptor for a supported source separation model."""

    name: str
    display_name: str
    filename: str
    description: str
    arch: str  # "roformer" or "mdx"
    recommended_device: str = "cuda"


# ── Registered SOTA models ──────────────────────────────────────────────────

_REGISTRY: dict[str, ModelInfo] = {
    "bs_roformer": ModelInfo(
        name="bs_roformer",
        display_name="BS-RoFormer",
        filename="model_bs_roformer_ep_317_sdr_12.9755.ckpt",
        description="Modèle RoFormer (SDR 12.98 dB).",
        arch="roformer",
    ),
    "mdx_net": ModelInfo(
        name="mdx_net",
        display_name="MDX-Net",
        filename="UVR-MDX-NET-Inst_HQ_3.onnx",
        description="Modèle MDX-Net HQ3.",
        arch="mdx",
    ),
}

MODELS: dict[str, ModelInfo] = _REGISTRY


class ModelManager:
    """Registry query methods."""

    @staticmethod
    def available_models() -> list[ModelInfo]:
        return list(_REGISTRY.values())

    @staticmethod
    def list_models() -> list[str]:
        return list(_REGISTRY.keys())

    @staticmethod
    def get_model(name: str) -> ModelInfo:
        try:
            return _REGISTRY[name]
        except KeyError:
            raise KeyError(
                f"Unknown model '{name}'. Available: {', '.join(_REGISTRY)}"
            ) from None

    @staticmethod
    def default_model() -> ModelInfo:
        return _REGISTRY["bs_roformer"]
