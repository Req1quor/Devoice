"""Qt worker thread for running source separation in the background."""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from devoice.config import DEFAULT_OUTPUT_SUBDIR
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

    Signals
    -------
    progress(int, str)
        (percentage, status_message)
    file_started(str)
        (filename)
    file_completed(str, dict)
        (filename, {"vocals": Path, "instru": Path, "instrumental": Path})
    file_error(str, str)
        (filename, error_message)
    all_completed()
        Emitted when batch is finished.
    """

    progress = pyqtSignal(int, str)
    file_started = pyqtSignal(str)
    file_completed = pyqtSignal(str, dict)
    file_error = pyqtSignal(str, str)
    all_completed = pyqtSignal()

    def __init__(
        self,
        files: Optional[list[Path | str]] = None,
        jobs: Optional[list[SeparationJob]] = None,
        model_name: str = "bs_roformer",
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

    def cancel(self) -> None:
        """Cancel execution cleanly."""
        self._cancel_requested = True

    def request_cancel(self) -> None:
        self._cancel_requested = True

    @property
    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    def run(self) -> None:
        total = len(self._jobs)
        if total == 0:
            self.all_completed.emit()
            return

        for idx, job in enumerate(self._jobs):
            if self._cancel_requested:
                logger.info("Annulation demandée par l'utilisateur.")
                break

            filename = job.input_path.name
            self.file_started.emit(filename)

            step_pct = int((idx / total) * 100)
            self.progress.emit(step_pct, f"Initialisation pour {filename}…")

            def on_progress(fraction: float, msg: str):
                overall_pct = int(((idx + fraction) / total) * 100)
                self.progress.emit(overall_pct, f"[{idx+1}/{total}] {filename} : {msg}")

            result = self._process_job(job, on_progress)

            if result.success:
                res_dict = {k: str(v) for k, v in result.output_files.items()}
                if "instrumental" in res_dict:
                    res_dict["instru"] = res_dict["instrumental"]
                self.file_completed.emit(filename, res_dict)
            else:
                self.file_error.emit(filename, result.error_message)

            end_pct = int(((idx + 1) / total) * 100)
            self.progress.emit(end_pct, f"{filename} terminé")

        self.all_completed.emit()

    def _process_job(
        self,
        job: SeparationJob,
        progress_callback: Optional[Any] = None,
    ) -> SeparationResult:
        """Run separation for a single job."""
        try:
            out_dir = job.output_dir or (
                job.input_path.parent / DEFAULT_OUTPUT_SUBDIR
            )
            out_dir.mkdir(parents=True, exist_ok=True)

            engine = SeparationEngine(
                model_name=self._model_name,
                output_dir=out_dir,
                output_format=job.output_format,
            )

            stems = engine.separate(job.input_path, progress_callback=progress_callback)

            return SeparationResult(
                job=job,
                output_files=stems,
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
