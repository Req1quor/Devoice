"""Core separation engine wrapping the Demucs API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch
from demucs.api import Separator

from devoice.model_manager import ModelManager

logger = logging.getLogger(__name__)


class SeparationEngine:
    """High-level wrapper around :class:`demucs.api.Separator`.

    Automatically selects CUDA when available, otherwise falls back to CPU.
    Uses ``shifts=1`` and ``overlap=0.25`` for a good quality / speed
    trade-off.

    Parameters
    ----------
    model_name:
        Internal Demucs model name (e.g. ``"htdemucs"``).
    device:
        Force a specific device string.  ``None`` → auto-detect.
    shifts:
        Number of random time shifts for prediction averaging.
    overlap:
        Overlap ratio between chunks (0.0–1.0).
    """

    def __init__(
        self,
        model_name: str = "htdemucs",
        device: Optional[str] = None,
        shifts: int = 1,
        overlap: float = 0.25,
    ) -> None:
        # Validate model name via the registry
        ModelManager.get_model(model_name)

        self._device: str = device or self._detect_device()
        self._model_name: str = model_name
        self._shifts: int = shifts
        self._overlap: float = overlap

        logger.info(
            "Initialising SeparationEngine  model=%s  device=%s  "
            "shifts=%d  overlap=%.2f",
            model_name,
            self._device,
            shifts,
            overlap,
        )

        self._separator: Separator = Separator(
            model=model_name,
            device=self._device,
            shifts=shifts,
            overlap=overlap,
        )

    # ── properties ──────────────────────────────────────────────────────

    @property
    def model_name(self) -> str:
        """Return the active model name."""
        return self._model_name

    @property
    def device(self) -> str:
        """Return the compute device in use."""
        return self._device

    @property
    def sample_rate(self) -> int:
        """Return the sample rate expected by the loaded model."""
        return self._separator.samplerate

    # ── device helpers ──────────────────────────────────────────────────

    @staticmethod
    def _detect_device() -> str:
        """Return ``'cuda'`` when a CUDA GPU is available, else ``'cpu'``."""
        if torch.cuda.is_available():
            dev = "cuda"
            logger.info(
                "CUDA available — using GPU: %s",
                torch.cuda.get_device_name(0),
            )
        else:
            dev = "cpu"
            logger.info("CUDA not available — falling back to CPU.")
        return dev

    @staticmethod
    def is_cuda_available() -> bool:
        """Return *True* when at least one CUDA device is detected."""
        return torch.cuda.is_available()

    # ── separation ──────────────────────────────────────────────────────

    def separate(self, audio_path: Path | str) -> dict[str, np.ndarray]:
        """Run source separation on *audio_path*.

        Returns
        -------
        dict[str, numpy.ndarray]
            Mapping of stem name → audio array (channels × samples).
            Always includes a synthetic ``"instrumental"`` stem that equals
            the sum of every non-vocal source.
        """
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info("Separating: %s", audio_path)

        # Demucs returns (origin, separated) where separated maps
        # stem name → torch.Tensor on the model's device.
        _origin, separated = self._separator.separate_audio_file(audio_path)

        stems: dict[str, np.ndarray] = {}
        instrumental: np.ndarray | None = None

        for stem_name, tensor in separated.items():
            # tensor shape: (channels, samples) on device → numpy on CPU
            arr: np.ndarray = tensor.cpu().numpy()
            stems[stem_name] = arr

            if stem_name.lower() != "vocals":
                instrumental = arr if instrumental is None else instrumental + arr

        if instrumental is not None:
            stems["instrumental"] = instrumental

        logger.info(
            "Separation complete — stems: %s",
            ", ".join(stems.keys()),
        )
        return stems

    def separate_to_files(
        self,
        audio_path: Path | str,
        output_dir: Path | str,
        stems_to_save: Optional[list[str]] = None,
        output_sample_rate: Optional[int] = None,
    ) -> dict[str, Path]:
        """Separate *audio_path* and write each requested stem to *output_dir*.

        Parameters
        ----------
        audio_path:
            Path to the input audio file.
        output_dir:
            Directory where stem WAV files are written.
        stems_to_save:
            Which stems to persist.  ``None`` → save all (including
            ``"instrumental"``).
        output_sample_rate:
            Sample rate for the saved files.  ``None`` → use the model's
            native rate.

        Returns
        -------
        dict[str, Path]
            Mapping of stem name → written file path.
        """
        audio_path = Path(audio_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stems = self.separate(audio_path)
        sr = output_sample_rate or self.sample_rate

        saved: dict[str, Path] = {}
        for name, arr in stems.items():
            if stems_to_save is not None and name not in stems_to_save:
                continue
            out_path = output_dir / f"{audio_path.stem}_{name}.wav"
            # soundfile expects (samples, channels)
            sf.write(str(out_path), arr.T, sr, subtype="FLOAT")
            saved[name] = out_path
            logger.info("Saved stem '%s' → %s", name, out_path)

        return saved
