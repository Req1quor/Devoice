"""Qt worker thread for running source separation in the background."""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import soundfile as sf
from PyQt6.QtCore import QThread, pyqtSignal

from devoice.audio_utils import convert_audio, normalize_audio
from devoice.config import DEFAULT_OUTPUT_SUBDIR, OUTPUT_FORMATS
from devoice.engine import SeparationEngine

logger = logging.getLogger(__name__)


# ── Job descriptor ──────────────────────────────────────────────────────────


@dataclass
class SeparationJob:
    """Describes one file to be separated."""

    input_path: Path
    output_dir: Optional[Path] = None
    output_format: str = "WAV (16-bit)"
    normalize: bool = False
    stems_to_save: Optional[list[str]] = field(default_factory=lambda: ["vocals", "instrumental"])


# ── Result descriptor ──────────────────────────────────────────────────────


@dataclass
class SeparationResult:
    """Outcome of a single :class:`SeparationJob`."""

    job: SeparationJob
    output_files: dict[str, Path] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""


# ── Worker thread ──────────────────────────────────────────────────────────


class SeparationWorker(QThread):
    """QThread that processes one or more audio files asynchronously.

    Signals (Primary UI)
    -------------------
    progress(int, str)
        ``(percentage, status_message)``
    file_started(str)
        ``(filename)``
    file_completed(str, dict)
        ``(filename, {"vocals": Path, "instru": Path, "instrumental": Path})``
    file_error(str, str)
        ``(filename, error_message)``
    all_completed()
        Emitted when every file has been processed.

    Signals (Batch / Object API)
    ----------------------------
    progress_update(int, int, str)
        ``(current_index, total_jobs, status_message)``
    job_completed(object)
        ``SeparationResult``
    error_occurred(str)
        Fatal engine-level error message
    """

    # Primary UI signals
    progress = pyqtSignal(int, str)
    file_started = pyqtSignal(str)
    file_completed = pyqtSignal(str, dict)
    file_error = pyqtSignal(str, str)
    all_completed = pyqtSignal()

    # Legacy/Extended signals
    progress_update = pyqtSignal(int, int, str)
    job_completed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        files: Optional[list[Path | str]] = None,
        jobs: Optional[list[SeparationJob]] = None,
        model_name: str = "htdemucs",
        output_format: str = "WAV (16-bit)",
        output_dir: Optional[Path | str] = None,
        normalize: bool = False,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(parent)
        self._model_name = model_name
        self._output_format = output_format
        self._output_dir = Path(output_dir) if output_dir else None
        self._normalize = normalize
        self._cancel_requested = False

        if jobs is not None:
            self._jobs = jobs
        elif files is not None:
            self._jobs = [
                SeparationJob(
                    input_path=Path(f),
                    output_dir=self._output_dir,
                    output_format=self._output_format,
                    normalize=self._normalize,
                )
                for f in files
            ]
        else:
            self._jobs = []

    # ── control ─────────────────────────────────────────────────────────

    def cancel(self) -> None:
        """Cancel execution cleanly."""
        self._cancel_requested = True

    def request_cancel(self) -> None:
        """Alias for cancel()."""
        self._cancel_requested = True

    @property
    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    # ── thread entry point ──────────────────────────────────────────────

    def run(self) -> None:
        total = len(self._jobs)
        if total == 0:
            self.all_completed.emit()
            return

        # 1. Load model
        try:
            self.progress.emit(0, "Chargement du modèle…")
            self.progress_update.emit(0, total, "Chargement du modèle…")
            engine = SeparationEngine(model_name=self._model_name)
        except Exception as exc:
            msg = f"Impossible de charger le modèle '{self._model_name}': {exc}"
            logger.error(msg)
            self.file_error.emit("Moteur", msg)
            self.error_occurred.emit(msg)
            self.all_completed.emit()
            return

        # 2. Process each job
        for idx, job in enumerate(self._jobs):
            if self._cancel_requested:
                logger.info("Annulation demandée par l'utilisateur.")
                break

            filename = job.input_path.name
            self.file_started.emit(filename)

            step_pct = int((idx / total) * 100)
            self.progress.emit(step_pct, f"Traitement de {filename}…")
            self.progress_update.emit(idx + 1, total, f"Traitement de {filename}…")

            result = self._process_job(engine, job)

            if result.success:
                # Convert results paths to str/Path dict with aliases
                res_dict = {k: str(v) for k, v in result.output_files.items()}
                if "instrumental" in res_dict:
                    res_dict["instru"] = res_dict["instrumental"]
                self.file_completed.emit(filename, res_dict)
                self.job_completed.emit(result)
            else:
                self.file_error.emit(filename, result.error_message)
                self.job_completed.emit(result)

            end_pct = int(((idx + 1) / total) * 100)
            self.progress.emit(end_pct, f"{filename} terminé")

        self.all_completed.emit()

    # ── per-job pipeline ────────────────────────────────────────────────

    def _process_job(
        self, engine: SeparationEngine, job: SeparationJob
    ) -> SeparationResult:
        """Run separation + format export."""
        try:
            out_dir = job.output_dir or (
                job.input_path.parent / DEFAULT_OUTPUT_SUBDIR
            )
            out_dir.mkdir(parents=True, exist_ok=True)

            # Separate into raw stems (channels x samples)
            stems = engine.separate(job.input_path)

            names_to_save = (
                job.stems_to_save
                if job.stems_to_save is not None
                else ["vocals", "instrumental"]
            )

            fmt_info = OUTPUT_FORMATS.get(job.output_format, OUTPUT_FORMATS.get("WAV (16-bit)", {}))
            target_ext = fmt_info.get("ext", ".wav")
            bit_depth = fmt_info.get("bit_depth", 16)
            bitrate = fmt_info.get("bitrate", None)
            sr = engine.sample_rate

            output_files: dict[str, Path] = {}

            for stem_name in names_to_save:
                arr = stems.get(stem_name)
                if arr is None:
                    continue

                if job.normalize:
                    arr = normalize_audio(arr)

                final_path = out_dir / f"{job.input_path.stem}_{stem_name}{target_ext}"

                # Native soundfile writing for WAV and FLAC (no ffmpeg needed)
                if target_ext == ".wav":
                    subtype = "PCM_16"
                    if bit_depth == 24:
                        subtype = "PCM_24"
                    elif bit_depth == 32:
                        subtype = "FLOAT"
                    sf.write(str(final_path), arr.T, sr, subtype=subtype)

                elif target_ext == ".flac":
                    subtype = "PCM_24" if bit_depth == 24 else "PCM_16"
                    sf.write(str(final_path), arr.T, sr, format="FLAC", subtype=subtype)

                else:
                    # Lossy formats like MP3/OGG: write temp WAV then convert
                    temp_wav = out_dir / f"{job.input_path.stem}_{stem_name}_temp.wav"
                    sf.write(str(temp_wav), arr.T, sr, subtype="PCM_16")
                    try:
                        convert_audio(
                            temp_wav,
                            final_path,
                            bitrate=bitrate,
                            bit_depth=bit_depth,
                        )
                    finally:
                        if temp_wav.exists():
                            temp_wav.unlink()

                output_files[stem_name] = final_path

            return SeparationResult(
                job=job,
                output_files=output_files,
                success=True,
            )

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Job failed for %s: %s\n%s", job.input_path, exc, tb)
            return SeparationResult(
                job=job,
                success=False,
                error_message=str(exc),
            )
