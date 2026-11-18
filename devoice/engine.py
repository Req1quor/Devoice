"""Core separation engine wrapping Demucs v4."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import soundfile as sf
import torch
import torchaudio as ta
from demucs.apply import BagOfModels, apply_model
from demucs.audio import AudioFile, convert_audio as demucs_convert_audio
from demucs.pretrained import get_model

from devoice.model_manager import ModelManager

logger = logging.getLogger(__name__)


class SeparationEngine:
    """High-level wrapper around Demucs v4 models.

    Automatically selects CUDA when available, otherwise falls back to CPU.
    Uses shifts=1 and overlap=0.25 for studio quality with optimal speed.
    """

    def __init__(
        self,
        model_name: str = "htdemucs",
        device: Optional[str] = None,
        shifts: int = 1,
        overlap: float = 0.25,
    ) -> None:
        ModelManager.get_model(model_name)

        self._device: str = device or self._detect_device()
        self._model_name: str = model_name
        self._shifts: int = shifts
        self._overlap: float = overlap

        logger.info(
            "Initialising SeparationEngine model=%s device=%s shifts=%d overlap=%.2f",
            model_name,
            self._device,
            shifts,
            overlap,
        )

        self._model = get_model(name=model_name)
        self._model.to(self._device)
        self._model.eval()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def device(self) -> str:
        return self._device

    @property
    def sample_rate(self) -> int:
        return self._model.samplerate

    @property
    def audio_channels(self) -> int:
        return self._model.audio_channels

    @property
    def sources(self) -> list[str]:
        return list(self._model.sources)

    # ── device helpers ──────────────────────────────────────────────────

    @staticmethod
    def _detect_device() -> str:
        if torch.cuda.is_available():
            dev = "cuda"
            logger.info("CUDA available — using GPU: %s", torch.cuda.get_device_name(0))
        else:
            dev = "cpu"
            logger.info("CUDA not available — falling back to CPU.")
        return dev

    @staticmethod
    def is_cuda_available() -> bool:
        return torch.cuda.is_available()

    # ── track loading ───────────────────────────────────────────────────

    def _load_track(self, track_path: Path) -> torch.Tensor:
        """Load audio track and resample/channel-match to model specifications."""
        wav = None

        # 1. Try Demucs AudioFile (FFmpeg backend) if available
        try:
            wav = AudioFile(track_path).read(
                streams=0,
                samplerate=self.sample_rate,
                channels=self.audio_channels,
            )
        except Exception:
            wav = None

        # 2. Try torchaudio backend
        if wav is None:
            try:
                raw_wav, sr = ta.load(str(track_path))
                wav = demucs_convert_audio(raw_wav, sr, self.sample_rate, self.audio_channels)
            except Exception:
                wav = None

        # 3. Try soundfile backend (handles WAV, FLAC, OGG, and modern MP3)
        if wav is None:
            try:
                data, sr = sf.read(str(track_path), dtype="float32")
                if data.ndim == 1:
                    raw_wav = torch.from_numpy(data).unsqueeze(0)
                else:
                    raw_wav = torch.from_numpy(data.T)
                wav = demucs_convert_audio(raw_wav, sr, self.sample_rate, self.audio_channels)
            except Exception as exc:
                raise RuntimeError(
                    f"Impossible de lire le fichier audio '{track_path.name}': {exc}"
                ) from exc

        return wav

    # ── separation ──────────────────────────────────────────────────────

    def separate(
        self,
        audio_path: Path | str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> dict[str, np.ndarray]:
        """Run source separation on audio_path.

        Parameters
        ----------
        audio_path:
            Path to audio file.
        progress_callback:
            Optional function called with fraction (0.0 to 1.0) as separation progresses.
        """
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        wav = self._load_track(audio_path)

        # Standardize for Demucs
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / (ref.std() + 1e-8)

        # Hook tqdm in demucs.apply to report real-time chunk progress
        import demucs.apply
        orig_tqdm = demucs.apply.tqdm.tqdm

        total_submodels = len(self._model.models) if isinstance(self._model, BagOfModels) else 1
        current_submodel = [0]

        class ProgressTqdmWrapper:
            def __init__(self, iterable, *args, **kwargs):
                self.iterable = iterable
                self.total_chunks = len(iterable) if hasattr(iterable, "__len__") else 1
                self.processed_chunks = 0

            def __iter__(self):
                for item in self.iterable:
                    yield item
                    self.processed_chunks += 1
                    if progress_callback:
                        sub_pct = self.processed_chunks / max(1, self.total_chunks)
                        overall_pct = (current_submodel[0] + sub_pct) / total_submodels
                        progress_callback(min(0.99, max(0.01, overall_pct)))
                current_submodel[0] += 1

        try:
            demucs.apply.tqdm.tqdm = ProgressTqdmWrapper
            with torch.no_grad():
                sources = apply_model(
                    self._model,
                    wav[None],
                    device=self._device,
                    shifts=self._shifts,
                    overlap=self._overlap,
                    split=True,
                    progress=True,
                )[0]
        finally:
            demucs.apply.tqdm.tqdm = orig_tqdm

        if progress_callback:
            progress_callback(1.0)

        # De-standardize
        sources = sources * (ref.std() + 1e-8) + ref.mean()

        stems: dict[str, np.ndarray] = {}
        for name, tensor in zip(self._model.sources, sources):
            stems[name] = tensor.cpu().numpy()

        # Synthetic instrumental stem = sum of non-vocal stems
        non_vocal = [tensor for name, tensor in zip(self._model.sources, sources) if name != "vocals"]
        if non_vocal:
            instru_tensor = sum(non_vocal)
            stems["instrumental"] = instru_tensor.cpu().numpy()
            stems["instru"] = stems["instrumental"]

        return stems
