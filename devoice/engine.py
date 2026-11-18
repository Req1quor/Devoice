"""State-of-the-art separation engine powered by UVR / BS-RoFormer / MDX-Net."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

import static_ffmpeg
import torch

from devoice.audio_utils import (
    apply_spectral_debleed,
    apply_subbass_filter,
    apply_true_peak_normalization,
)
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
        subbass_filter: bool = True,
        true_peak: bool = True,
        spectral_debleed: bool = False,
    ) -> None:
        self.model_info = ModelManager.get_model(model_name)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "devoice_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = output_format

        # Pro audio post-processing flags
        self.subbass_filter = subbass_filter
        self.true_peak = true_peak
        self.spectral_debleed = spectral_debleed

        # Model cache in user appdata/home
        self.cache_dir = Path.home() / ".cache" / "devoice" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._separator = None

        # Speed optimization for CUDA
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True

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
            return f"● {name} (CUDA)"
        return "● CPU"

    # ── Engine initialization ───────────────────────────────────────────

    def _init_separator(self):
        """Lazy-initialize audio-separator instance with GPU batch tuning."""
        # Ensure static ffmpeg is on PATH right before initializing
        static_ffmpeg.add_paths()

        from audio_separator.separator import Separator

        # Configure output format
        fmt = "WAV"
        if "FLAC" in self.output_format.upper():
            fmt = "FLAC"
        elif "MP3" in self.output_format.upper():
            fmt = "MP3"

        gpu_batch_size = 4 if torch.cuda.is_available() else 1

        mdx_params = {
            "hop_length": 1024,
            "segment_size": 256,
            "overlap": 0.25,
            "batch_size": gpu_batch_size,
            "enable_denoise": False,
        }

        mdxc_params = {
            "segment_size": 256,
            "batch_size": gpu_batch_size,
            "overlap": 8,
        }

        logger.info(
            "Initializing Separator for %s (%s) -> batch_size=%d",
            self.model_info.display_name,
            self.model_info.filename,
            gpu_batch_size,
        )

        self._separator = Separator(
            model_file_dir=str(self.cache_dir),
            output_dir=str(self.output_dir),
            output_format=fmt,
            normalization_threshold=0.95,
            mdx_params=mdx_params,
            mdxc_params=mdxc_params,
        )

        logger.info("Loading model %s...", self.model_info.filename)
        self._separator.load_model(model_filename=self.model_info.filename)

    # ── Separation ──────────────────────────────────────────────────────

    def separate(
        self,
        audio_path: Path | str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> dict[str, Path]:
        """Separate audio into isolated vocals and instrumental tracks."""
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        if progress_callback:
            progress_callback(0.05, f"Initialisation du modèle {self.model_info.name}…")

        if self._separator is None:
            self._init_separator()

        if progress_callback:
            progress_callback(0.15, "Standardisation audio…")

        # Pre-convert to a clean PCM WAV to eliminate any audioread/ID3/EOF tag issues
        clean_input = self.output_dir / f"_clean_{audio_path.stem}.wav"
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        conv_cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(audio_path),
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(clean_input),
        ]
        try:
            subprocess.run(conv_cmd, capture_output=True, check=True)
            target_input = clean_input
        except Exception as exc:
            logger.warning("Direct WAV conversion failed (%s), using original file", exc)
            target_input = audio_path

        if progress_callback:
            progress_callback(0.25, "Séparation en cours (calcul spectral haute précision)…")

        try:
            output_files = self._separator.separate(str(target_input))
        finally:
            if clean_input.exists():
                try:
                    clean_input.unlink()
                except Exception:
                    pass

        if progress_callback:
            progress_callback(0.85, "Organisation et post-traitements studio…")

        results: dict[str, Path] = {}

        for fname in output_files:
            file_path = self.output_dir / fname
            if not file_path.exists():
                cand = Path(fname)
                if cand.exists():
                    file_path = cand

            # Rename if clean prefix exists
            if file_path.exists() and "_clean_" in file_path.name:
                cleaned_name = file_path.name.replace("_clean_", "")
                dest_path = file_path.parent / cleaned_name
                try:
                    shutil.move(str(file_path), str(dest_path))
                    file_path = dest_path
                except Exception:
                    pass

            lower_name = file_path.name.lower()
            if "(vocals)" in lower_name or "vocals" in lower_name:
                results["vocals"] = file_path
            elif "(instrumental)" in lower_name or "instrumental" in lower_name or "inst" in lower_name:
                results["instrumental"] = file_path
                results["instru"] = file_path

        if "vocals" not in results and len(output_files) >= 1:
            results["vocals"] = self.output_dir / output_files[0]
        if "instrumental" not in results and len(output_files) >= 2:
            results["instrumental"] = self.output_dir / output_files[1]
            results["instru"] = results["instrumental"]

        # ── Pro Audio Post-Processing (Non-destructive) ─────────────────
        vocals_path = results.get("vocals")
        instru_path = results.get("instrumental")

        if vocals_path and vocals_path.is_file():
            # 1. Sub-bass rumble cutoff (< 65 Hz)
            if self.subbass_filter:
                try:
                    apply_subbass_filter(vocals_path, cutoff_hz=65.0)
                except Exception as exc:
                    logger.warning("Could not apply sub-bass filter: %s", exc)

            # 2. Spectral de-bleed
            if self.spectral_debleed and instru_path and instru_path.is_file():
                try:
                    apply_spectral_debleed(vocals_path, instru_path, reduction_db=2.5)
                except Exception as exc:
                    logger.warning("Could not apply spectral de-bleed: %s", exc)

            # 3. True-Peak Normalization (-1.0 dBFS)
            if self.true_peak:
                try:
                    apply_true_peak_normalization(vocals_path, target_dbfs=-1.0)
                    if instru_path:
                        apply_true_peak_normalization(instru_path, target_dbfs=-1.0)
                except Exception as exc:
                    logger.warning("Could not apply True-Peak normalization: %s", exc)

        if progress_callback:
            progress_callback(1.0, "Prêt !")

        return results
