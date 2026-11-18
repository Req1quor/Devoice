"""State-of-the-art separation engine powered by UVR / BS-RoFormer / MDX-Net."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Callable, Optional

import static_ffmpeg
import torch

from devoice.model_manager import ModelManager

logger = logging.getLogger(__name__)

# Ensure portable FFmpeg is on PATH
try:
    static_ffmpeg.add_paths()
except Exception as exc:
    logger.warning("Could not add static-ffmpeg paths: %s", exc)


class SeparationEngine:
    """Unified engine for RoFormer and MDX-Net source separation.

    Supports automatic GPU/CUDA acceleration with graceful CPU fallback.
    """

    def __init__(
        self,
        model_name: str = "bs_roformer",
        output_dir: Optional[Path | str] = None,
        output_format: str = "WAV",
    ) -> None:
        self.model_info = ModelManager.get_model(model_name)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "devoice_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = output_format

        # Model cache in user appdata/home
        self.cache_dir = Path.home() / ".cache" / "devoice" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._separator = None

    # ── Device detection ────────────────────────────────────────────────

    @staticmethod
    def is_cuda_available() -> bool:
        """Check if CUDA-enabled GPU is accessible."""
        return torch.cuda.is_available()

    @property
    def device_info(self) -> str:
        """Return human-readable device name."""
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return f"⚡ GPU : {name}"
        return "💻 CPU"

    # ── Engine initialization ───────────────────────────────────────────

    def _init_separator(self):
        """Lazy-initialize audio-separator instance."""
        from audio_separator.separator import Separator

        # Configure output format
        fmt = "WAV"
        if "FLAC" in self.output_format.upper():
            fmt = "FLAC"
        elif "MP3" in self.output_format.upper():
            fmt = "MP3"

        logger.info(
            "Initializing Separator for %s (%s) -> format %s",
            self.model_info.display_name,
            self.model_info.filename,
            fmt,
        )

        self._separator = Separator(
            model_file_dir=str(self.cache_dir),
            output_dir=str(self.output_dir),
            output_format=fmt,
            normalization_threshold=0.95,
        )

        logger.info("Loading model %s...", self.model_info.filename)
        self._separator.load_model(model_filename=self.model_info.filename)

    # ── Separation ──────────────────────────────────────────────────────

    def separate(
        self,
        audio_path: Path | str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> dict[str, Path]:
        """Separate audio into isolated vocals and instrumental tracks.

        Returns
        -------
        dict[str, Path]
            Dictionary containing "vocals", "instrumental" (and "instru") paths.
        """
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        if progress_callback:
            progress_callback(0.05, f"Initialisation du modèle {self.model_info.name}…")

        if self._separator is None:
            self._init_separator()

        if progress_callback:
            progress_callback(0.15, "Séparation en cours (calcul spectral)…")

        # Run UVR/RoFormer/MDX separation
        output_files = self._separator.separate(str(audio_path))

        if progress_callback:
            progress_callback(0.90, "Organisation des fichiers séparés…")

        results: dict[str, Path] = {}

        # audio-separator produces files containing "(Vocals)" and "(Instrumental)"
        for fname in output_files:
            file_path = self.output_dir / fname
            if not file_path.exists():
                # In case relative path was returned
                cand = Path(fname)
                if cand.exists():
                    file_path = cand

            lower_name = fname.lower()
            if "(vocals)" in lower_name or "vocals" in lower_name:
                results["vocals"] = file_path
            elif "(instrumental)" in lower_name or "instrumental" in lower_name or "inst" in lower_name:
                results["instrumental"] = file_path
                results["instru"] = file_path

        # If for any reason stems couldn't be matched by name, map by order
        if "vocals" not in results and len(output_files) >= 1:
            results["vocals"] = self.output_dir / output_files[0]
        if "instrumental" not in results and len(output_files) >= 2:
            results["instrumental"] = self.output_dir / output_files[1]
            results["instru"] = results["instrumental"]

        if progress_callback:
            progress_callback(1.0, "Séparation terminée avec succès !")

        return results
