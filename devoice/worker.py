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
    subbass_filter: bool = True
    subbass_cutoff: float = 65.0
    deesser: bool = False
    deesser_freq: float = 7200.0
    dereverb: bool = False
    silence_purifier: bool = True
    vocal_leveler: bool = True
    true_peak: bool = True
    spectral_debleed: bool = False


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
        subbass_filter: bool = True,
        subbass_cutoff: float = 65.0,
        deesser: bool = False,
        deesser_freq: float = 7200.0,
        dereverb: bool = False,
        silence_purifier: bool = True,
        vocal_leveler: bool = True,
        true_peak: bool = True,
        spectral_debleed: bool = False,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(parent)
        self._model_name = model_name
        self._output_format = output_format
        self._output_dir = Path(output_dir) if output_dir else None
        self._subbass_filter = subbass_filter
        self._subbass_cutoff = subbass_cutoff
        self._deesser = deesser
        self._deesser_freq = deesser_freq
        self._dereverb = dereverb
        self._silence_purifier = silence_purifier
        self._vocal_leveler = vocal_leveler
        self._true_peak = true_peak
        self._spectral_debleed = spectral_debleed
        self._cancel_requested = False

        if jobs is not None:
            self._jobs = jobs
        elif files is not None:
            self._jobs = [
                SeparationJob(
                    input_path=Path(f),
                    output_dir=self._output_dir,
                    output_format=self._output_format,
                    subbass_filter=self._subbass_filter,
                    subbass_cutoff=self._subbass_cutoff,
                    deesser=self._deesser,
                    deesser_freq=self._deesser_freq,
                    dereverb=self._dereverb,
                    silence_purifier=self._silence_purifier,
                    vocal_leveler=self._vocal_leveler,
                    true_peak=self._true_peak,
                    spectral_debleed=self._spectral_debleed,
                )
                for f in files
            ]
        else:
            self._jobs = []

    def cancel(self) -> None:
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
                subbass_filter=job.subbass_filter,
                subbass_cutoff=job.subbass_cutoff,
                deesser=job.deesser,
                deesser_freq=job.deesser_freq,
                dereverb=job.dereverb,
                silence_purifier=job.silence_purifier,
                vocal_leveler=job.vocal_leveler,
                true_peak=job.true_peak,
                spectral_debleed=job.spectral_debleed,
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


# ── YouTube Download Worker ──────────────────────────────────────────────────


class YouTubeDownloadWorker(QThread):
    """QThread for downloading audio from YouTube asynchronously."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(Path)
    error = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        output_dir: Optional[Path | str] = None,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.output_dir = Path(output_dir) if output_dir else (Path.home() / "Downloads" / "Devoice")
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        from devoice.youtube import download_youtube_audio

        def callback(pct: int, msg: str) -> None:
            if not self._cancelled:
                self.progress.emit(pct, msg)

        try:
            downloaded = download_youtube_audio(
                self.url,
                self.output_dir,
                progress_callback=callback,
            )
            if not self._cancelled:
                self.finished.emit(downloaded)
        except Exception as exc:
            if not self._cancelled:
                logger.exception("YouTube download failed: %s", exc)
                self.error.emit(str(exc))

