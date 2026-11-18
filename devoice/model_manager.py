"""Model registry, metadata, and local cache management for Demucs models."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)

# ── Model metadata ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ModelInfo:
    """Immutable descriptor for a supported Demucs model."""

    name: str
    display_name: str
    description: str
    is_fine_tuned: bool = False
    default_sources: tuple[str, ...] = ("drums", "bass", "other", "vocals")


# ── Built-in registry ──────────────────────────────────────────────────────

_REGISTRY: dict[str, ModelInfo] = {
    "htdemucs": ModelInfo(
        name="htdemucs",
        display_name="HTDemucs",
        description=(
            "Hybrid Transformer Demucs — good balance of speed and quality. "
            "Recommended for most use-cases."
        ),
        is_fine_tuned=False,
    ),
    "htdemucs_ft": ModelInfo(
        name="htdemucs_ft",
        display_name="HTDemucs (Fine-Tuned)",
        description=(
            "Fine-tuned variant of HTDemucs. Higher separation quality at the "
            "cost of longer processing time."
        ),
        is_fine_tuned=True,
    ),
}


class ModelManager:
    """Discover, cache, and serve Demucs model metadata.

    Parameters
    ----------
    cache_dir:
        Optional directory for downloaded model weights.  When *None* the
        default ``torch.hub`` cache is used.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache_dir: Path | None = cache_dir
        if self._cache_dir is not None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            torch.hub.set_dir(str(self._cache_dir))

    # ── queries ─────────────────────────────────────────────────────────

    @staticmethod
    def available_models() -> list[ModelInfo]:
        """Return the list of all registered models."""
        return list(_REGISTRY.values())

    @staticmethod
    def get_model(name: str) -> ModelInfo:
        """Look up a model by its internal name.

        Raises
        ------
        KeyError
            If *name* is not in the registry.
        """
        try:
            return _REGISTRY[name]
        except KeyError:
            raise KeyError(
                f"Unknown model '{name}'. "
                f"Available: {', '.join(_REGISTRY)}"
            ) from None

    @staticmethod
    def default_model() -> ModelInfo:
        """Return the recommended default model."""
        return _REGISTRY["htdemucs"]

    # ── cache helpers ───────────────────────────────────────────────────

    def cache_directory(self) -> Path:
        """Return the resolved cache directory for model weights."""
        if self._cache_dir is not None:
            return self._cache_dir
        return Path(torch.hub.get_dir())

    def is_model_cached(self, name: str) -> bool:
        """Check whether weights for *name* are already on disk.

        This performs a best-effort search of the hub-cache checkpoints
        directory for a file whose name contains *name*.
        """
        cache = self.cache_directory() / "checkpoints"
        if not cache.exists():
            return False
        return any(name in p.name for p in cache.iterdir())

    def clear_cache(self) -> int:
        """Remove all cached model files and return the count deleted."""
        cache = self.cache_directory() / "checkpoints"
        if not cache.exists():
            return 0
        count = 0
        for path in cache.iterdir():
            if path.is_file():
                path.unlink()
                count += 1
                logger.info("Deleted cached model file: %s", path)
        return count
