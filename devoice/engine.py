"""State-of-the-art separation engine powered by UVR / BS-RoFormer / MDX-Net."""

from __future__ import annotations

import logging
import math
import shutil
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

import soundfile as sf
import static_ffmpeg

try:
    import torch
except Exception:
    torch = None

from devoice.audio_utils import (
    DSPRackConfig,
    apply_true_peak_normalization,
    process_dsp_rack,
    write_audio_file,
)
from devoice.model_manager import ModelManager
from devoice.runtime_manager import ensure_ffmpeg_paths, get_models_dir

logger = logging.getLogger(__name__)

# Ensure portable FFmpeg is on PATH
try:
    ensure_ffmpeg_paths()
except Exception as exc:
    logger.warning("Could not add ffmpeg paths: %s", exc)


class SeparationEngine:
    """Unified engine for RoFormer and MDX-Net with a tailored studio DSP chain."""

    def __init__(
        self,
        model_name: str = "bs_roformer",
        output_dir: Path | str | None = None,
        output_format: str = "WAV",
        subbass_filter: bool = True,
        subbass_cutoff: float = 65.0,
        deesser: bool = False,
        deesser_freq: float = 7200.0,
        dereverb: bool = False,
        silence_purifier: bool = True,
        vocal_leveler: bool = True,
        true_peak: bool = True,
        spectral_debleed: bool = False,
    ) -> None:
        self.model_info = ModelManager.get_model(model_name)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "devoice_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = output_format

        # Tailored Studio DSP settings
        self.subbass_filter = subbass_filter
        self.subbass_cutoff = subbass_cutoff
        self.deesser = deesser
        self.deesser_freq = deesser_freq
        self.dereverb = dereverb
        self.silence_purifier = silence_purifier
        self.vocal_leveler = vocal_leveler
        self.true_peak = true_peak
        self.spectral_debleed = spectral_debleed

        # Model cache in user chosen drive (preserves C: disk space)
        self.cache_dir = get_models_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._separator = None

        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True

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

    def _init_separator(self):
        """Lazy-initialize audio-separator instance with GPU batch tuning."""
        ensure_ffmpeg_paths()

        from audio_separator.separator import Separator

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

    def separate(
        self,
        audio_path: Path | str,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> dict[str, Path]:
        """Separate audio into isolated vocals and instrumental tracks with studio post-processing."""
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

        if progress_callback:
            progress_callback(0.05, "Chargement du modèle…")

        if self._separator is None:
            self._init_separator()

        # Smooth real-time progress ticker during neural inference
        ticker_stop = threading.Event()

        def _ticker():
            t0 = time.time()
            while not ticker_stop.is_set():
                elapsed = time.time() - t0
                frac = 0.20 + 0.62 * (1.0 - math.exp(-elapsed / 14.0))
                if progress_callback:
                    progress_callback(frac, f"Séparation en cours… ({int(frac * 100)}%)")
                ticker_stop.wait(0.35)

        ticker_thread = threading.Thread(target=_ticker, daemon=True)
        if progress_callback:
            ticker_thread.start()

        try:
            try:
                output_files = self._separator.separate(str(audio_path))
            except Exception as exc:
                logger.warning("Séparation directe échouée (%s), conversion de secours", exc)
                clean_input = self.output_dir / f"_clean_{audio_path.stem}.wav"
                ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
                conv_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-i",
                    str(audio_path),
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_f32le",
                    str(clean_input),
                ]
                subprocess.run(conv_cmd, capture_output=True, check=True)
                try:
                    output_files = self._separator.separate(str(clean_input))
                finally:
                    if clean_input.exists():
                        try:
                            clean_input.unlink()
                        except Exception:
                            pass
        finally:
            ticker_stop.set()
            if ticker_thread.is_alive():
                ticker_thread.join(timeout=1.0)

        if progress_callback:
            progress_callback(0.85, "Finalisation des pistes…")

        results: dict[str, Path] = {}

        for fname in output_files:
            file_path = self.output_dir / fname
            if not file_path.exists():
                cand = Path(fname)
                if cand.exists():
                    file_path = cand

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

        # ── Raw Stems Retention & Caching ───────────────────────────────
        vocals_path = results.get("vocals")
        instru_path = results.get("instrumental")

        raw_vocals_path: Path | None = None
        raw_instru_path: Path | None = None

        if vocals_path and vocals_path.is_file():
            raw_vocals_path = vocals_path.parent / f"{vocals_path.stem}_raw{vocals_path.suffix}"
            shutil.copy2(str(vocals_path), str(raw_vocals_path))
            results["raw_vocals"] = raw_vocals_path

        if instru_path and instru_path.is_file():
            raw_instru_path = instru_path.parent / f"{instru_path.stem}_raw{instru_path.suffix}"
            shutil.copy2(str(instru_path), str(raw_instru_path))
            results["raw_instrumental"] = raw_instru_path
            results["raw_instru"] = raw_instru_path

        # ── Tailored Studio DSP Chain (In-Memory from Raw Stem) ─────────
        if raw_vocals_path and raw_vocals_path.is_file():
            if progress_callback:
                progress_callback(0.92, "Application du DSP studio…")
            rack_config = DSPRackConfig(
                enabled=True,
                silence_purifier=self.silence_purifier,
                subbass_filter=self.subbass_filter,
                subbass_cutoff=self.subbass_cutoff,
                dereverb=self.dereverb,
                deesser=self.deesser,
                deesser_freq=self.deesser_freq,
                vocal_leveler=self.vocal_leveler,
                spectral_debleed=self.spectral_debleed,
                true_peak=self.true_peak,
            )
            try:
                self.reprocess_stem(
                    raw_vocals_path=raw_vocals_path,
                    output_path=vocals_path,
                    config=rack_config,
                    instru_path=raw_instru_path or instru_path,
                )
            except Exception as exc:
                logger.warning("Could not execute DSP rack during initial separation: %s", exc)

        if self.true_peak and instru_path and instru_path.is_file():
            if progress_callback:
                progress_callback(0.98, "Ajustement du niveau instrumental…")
            try:
                apply_true_peak_normalization(instru_path, target_dbfs=-1.0)
            except Exception as exc:
                logger.warning("Could not apply True-Peak normalization: %s", exc)

        if progress_callback:
            progress_callback(1.0, "Prêt !")

        return results

    def reprocess_stem(
        self,
        raw_vocals_path: Path | str,
        output_path: Path | str,
        config: DSPRackConfig,
        instru_path: Path | str | None = None,
    ) -> Path:
        """Execute DSP rack reprocessing on raw vocal stem without running neural inference."""
        raw_v_path = Path(raw_vocals_path)
        out_path = Path(output_path)
        if raw_v_path.resolve() == out_path.resolve():
            raise ValueError("output_path must not overwrite raw_vocals_path")
        if not raw_v_path.is_file():
            raise FileNotFoundError(f"Raw vocals file not found: {raw_v_path}")

        vocals_data, sr = sf.read(str(raw_v_path), dtype="float32")

        instru_data = None
        if instru_path:
            i_path = Path(instru_path)
            if i_path.is_file():
                try:
                    instru_data, _ = sf.read(str(i_path), dtype="float32")
                except Exception as exc:
                    logger.warning("Could not load instrumental stem for debleed: %s", exc)

        processed_data = process_dsp_rack(vocals_data, sr, config, instru=instru_data)
        write_audio_file(out_path, processed_data, sr)
        return out_path
