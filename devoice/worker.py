"""Qt worker thread for running source separation in the background."""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from devoice.audio_utils import convert_audio, normalize_audio
from devoice.config import DEFAULT_OUTPUT_SUBDIR, OUTPUT_FORMATS
from devoice.engine import SeparationEngine

logger = logging.getLogger(__name__)


# ── Job descriptor ──────────────────────────────────────────────────────────


@dataclass
class SeparationJob:
    """Describes one file to be separated.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    output_dir:
        Directory for the output stems.  ``None`` → sibling
        ``devoice_output/`` directory next to the input file.
    output_format:
        Display-name key into :data:`devoice.config.OUTPUT_FORMATS`.
    normalize:
        Whether to peak-normalise the output stems.
    stems_to_save:
        Which stems to write.  ``None`` → vocals + instrumental.
    """

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
    """QThread that processes one or more :class:`SeparationJob` items.

    Signals
    -------
    progress_update(int, int, str)
        ``(current_index, total_jobs, status_message)``
    job_completed(SeparationResult)
        Emitted after each individual job finishes (success **or** failure).
    all_completed(list)
        Emitted once when every job in the batch has been processed.
        Payload is a ``list[SeparationResult]``.
    error_occurred(str)
        Emitted for fatal engine-level errors that abort the whole batch.
    """

    progress_update = pyqtSignal(int, int, str)
    job_completed = pyqtSignal(object)  # SeparationResult
    all_completed = pyqtSignal(list)  # list[SeparationResult]
    error_occurred = pyqtSignal(str)  # error message

    def __init__(
        self,
        jobs: list[SeparationJob],
        model_name: str = "htdemucs",
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._jobs = jobs
        self._model_name = model_name
        self._cancel_requested = False

    # ── control ─────────────────────────────────────────────────────────

    def request_cancel(self) -> None:
        """Ask the worker to stop after the current job finishes."""
        self._cancel_requested = True

    @property
    def is_cancel_requested(self) -> bool:
        """Whether cancellation has been requested."""
        return self._cancel_requested

    # ── thread entry point ──────────────────────────────────────────────

    def run(self) -> None:  # noqa: C901 (complexity justified by batch loop)
        """Execute the separation pipeline on each queued job."""
        results: list[SeparationResult] = []
        total = len(self._jobs)

        # Build the engine once for the entire batch
        try:
            self.progress_update.emit(0, total, "Loading model…")
            engine = SeparationEngine(model_name=self._model_name)
        except Exception as exc:
            msg = f"Failed to load model '{self._model_name}': {exc}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            return

        for idx, job in enumerate(self._jobs):
            if self._cancel_requested:
                logger.info("Cancellation requested — stopping batch.")
                break

            file_label = job.input_path.name
            self.progress_update.emit(
                idx + 1,
                total,
                f"Processing {file_label} ({idx + 1}/{total})…",
            )

            result = self._process_job(engine, job)
            results.append(result)
            self.job_completed.emit(result)

        self.all_completed.emit(results)

    # ── per-job pipeline ────────────────────────────────────────────────

    def _process_job(
        self, engine: SeparationEngine, job: SeparationJob
    ) -> SeparationResult:
        """Run separation + optional normalisation + format conversion."""
        try:
            # Resolve output directory
            out_dir = job.output_dir or (
                job.input_path.parent / DEFAULT_OUTPUT_SUBDIR
            )
            out_dir.mkdir(parents=True, exist_ok=True)

            # 1. Separate into raw stems (WAV float)
            stems = engine.separate(job.input_path)

            # 2. Determine which stems to save
            names_to_save = (
                job.stems_to_save
                if job.stems_to_save is not None
                else list(stems.keys())
            )

            # 3. Optionally normalise, then write to disk
            fmt_info = OUTPUT_FORMATS.get(job.output_format)
            if fmt_info is None:
                raise ValueError(
                    f"Unknown output format '{job.output_format}'. "
                    f"Available: {', '.join(OUTPUT_FORMATS)}"
                )

            sr = engine.sample_rate
            output_files: dict[str, Path] = {}

            for stem_name in names_to_save:
                arr = stems.get(stem_name)
                if arr is None:
                    logger.warning(
                        "Requested stem '%s' not produced — skipping.",
                        stem_name,
                    )
                    continue

                # Normalise if requested
                if job.normalize:
                    arr = normalize_audio(arr)

                # Write an intermediate WAV first (lossless)
                import soundfile as _sf

                temp_wav = out_dir / f"{job.input_path.stem}_{stem_name}.wav"
                _sf.write(str(temp_wav), arr.T, sr, subtype="FLOAT")

                target_ext = fmt_info["ext"]
                final_path = out_dir / f"{job.input_path.stem}_{stem_name}{target_ext}"

                if target_ext == ".wav":
                    # Re-encode to the requested bit depth directly
                    convert_audio(
                        temp_wav,
                        final_path,
                        bit_depth=fmt_info.get("bit_depth"),
                    )
                    # Remove temp only when different from final
                    if temp_wav != final_path and temp_wav.exists():
                        temp_wav.unlink()
                else:
                    convert_audio(
                        temp_wav,
                        final_path,
                        bitrate=fmt_info.get("bitrate"),
                        bit_depth=fmt_info.get("bit_depth"),
                    )
                    if temp_wav.exists():
                        temp_wav.unlink()

                output_files[stem_name] = final_path
                logger.info("Wrote %s → %s", stem_name, final_path)

            return SeparationResult(
                job=job,
                output_files=output_files,
                success=True,
            )

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error(
                "Job failed for %s: %s\n%s", job.input_path, exc, tb
            )
            return SeparationResult(
                job=job,
                success=False,
                error_message=str(exc),
            )
