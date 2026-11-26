"""Devoice Dynamic Runtime Manager.

Manages dynamic on-demand acquisition, verification, and loading of PyTorch,
CUDA acceleration libraries, and neural stem separation runtimes.
Enables a lightweight (< 90 MB) core installer with first-launch hardware-adaptive
runtime deployment.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_ffmpeg_paths() -> None:
    """Ensure bundled ffmpeg and ffprobe are on PATH without triggering network downloads."""
    import shutil

    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "win32")
            candidates.append(Path(sys._MEIPASS))
        app_dir = Path(sys.executable).parent
        candidates.append(app_dir / "_internal" / "win32")
        candidates.append(app_dir / "win32")
        candidates.append(app_dir)
    else:
        root = Path(__file__).resolve().parent.parent
        candidates.append(root / "dist" / "Devoice" / "_internal" / "win32")
        candidates.append(root / "dist" / "Devoice" / "win32")
        candidates.append(root / "packaging" / "win32")
        candidates.append(root / "packaging")

    for cand in candidates:
        if cand and (cand / "ffmpeg.exe").exists():
            cand_str = str(cand.resolve())
            if cand_str not in os.environ.get("PATH", ""):
                os.environ["PATH"] = cand_str + os.pathsep + os.environ.get("PATH", "")
            break


def get_app_dir() -> Path:
    """Return the base directory of the Devoice application."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def is_directory_writable(path: Path) -> bool:
    """Check if the given directory can be created and written to."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        return True
    except Exception:
        return False


def get_runtime_dir() -> Path:
    """Return the persistent directory where the AI audio runtime is installed.

    Respects the drive where the user installed Devoice (e.g. E: drive) to avoid
    filling up the C: system disk with CUDA and PyTorch.

    Order of resolution:
    1. Candidate next to the application (e.g. {app}\\runtime from installer).
    2. Saved path in Windows registry / QSettings ("runtime_dir").
    3. Dedicated folder on the application drive (e.g. E:\\Devoice\\runtime).
    4. Fallback to %LOCALAPPDATA%\\Devoice\\runtime if no other drive is writable.
    """
    app_dir = get_app_dir()

    # 1. First priority: Bundled runtime right next to Devoice.exe
    cand_app = app_dir / "runtime"
    if cand_app.exists() and (cand_app / "torch").exists():
        return cand_app

    # 2. User setting from QSettings registry
    try:
        from PyQt6.QtCore import QSettings

        settings = QSettings("Devoice", "Devoice")
        saved = settings.value("runtime_dir", "")
        if saved:
            p = Path(saved)
            if p.exists() and (p / "torch").exists():
                return p
    except Exception:
        pass

    # 3. Check if installed on a non-C drive (e.g. E:\Devoice\runtime)
    if app_dir.drive and app_dir.drive.upper() != "C:":
        cand_drive = Path(app_dir.drive + "\\") / "Devoice" / "runtime"
        if cand_drive.exists() and (cand_drive / "torch").exists():
            return cand_drive

    # 4. If nothing exists yet, prefer the application directory if writable
    if is_directory_writable(cand_app):
        return cand_app

    # 5. If app_dir was admin-protected on E:, use E:\Devoice\runtime
    if app_dir.drive and app_dir.drive.upper() != "C:":
        cand_drive = Path(app_dir.drive + "\\") / "Devoice" / "runtime"
        if is_directory_writable(cand_drive):
            return cand_drive

    # 6. Fallback to LocalAppData
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Devoice" / "runtime"
    return Path.home() / ".cache" / "devoice" / "runtime"


def get_models_dir() -> Path:
    """Return the persistent directory where AI stem separation models are cached.

    Preserves space on C: by storing models on the same drive as the runtime.
    """
    try:
        from PyQt6.QtCore import QSettings

        settings = QSettings("Devoice", "Devoice")
        saved = settings.value("models_dir", "")
        if saved and Path(saved).exists():
            return Path(saved)
    except Exception:
        pass

    runtime_parent = get_runtime_dir().parent
    cand_models = runtime_parent / "models"
    if cand_models.exists() or is_directory_writable(cand_models):
        return cand_models

    app_dir = get_app_dir()
    if app_dir.drive and app_dir.drive.upper() != "C:":
        cand_drive = Path(app_dir.drive + "\\") / "Devoice" / "models"
        if cand_drive.exists() or is_directory_writable(cand_drive):
            return cand_drive

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Devoice" / "models"
    return Path.home() / ".cache" / "devoice" / "models"


def setup_runtime_environment(runtime_dir: Path | None = None) -> bool:
    """Inject runtime directory into sys.path and Windows DLL search path.

    Must be called before importing torch or heavy ML dependencies.
    Also redirects TORCH_HOME and HF_HOME away from C: to the chosen drive.
    """
    if runtime_dir is None:
        runtime_dir = get_runtime_dir()

    # Route AI model caches away from C: to the user's chosen drive
    try:
        models_dir = get_models_dir()
        models_dir.mkdir(parents=True, exist_ok=True)
        os.environ["TORCH_HOME"] = str(models_dir / "torch")
        os.environ["HF_HOME"] = str(models_dir / "huggingface")
    except Exception:
        pass

    if not runtime_dir.exists():
        return False

    runtime_str = str(runtime_dir)
    if runtime_str not in sys.path:
        sys.path.insert(0, runtime_str)

    # Windows DLL directory registration (Python 3.8+)
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        # Torch lib contains torch_cuda.dll, cudnn, cublas, etc.
        torch_lib = runtime_dir / "torch" / "lib"
        if torch_lib.exists():
            try:
                os.add_dll_directory(str(torch_lib))
            except Exception as e:
                logger.debug("Failed to add torch_lib to dll directory: %s", e)

        # Main runtime root for general DLLs
        try:
            os.add_dll_directory(str(runtime_dir))
        except Exception as e:
            logger.debug("Failed to add runtime_dir to dll directory: %s", e)

    return True


def is_torch_available() -> bool:
    """Check if PyTorch can be successfully imported and initialized."""
    # First ensure runtime environment paths are hooked
    setup_runtime_environment()

    try:
        import torch  # type: ignore

        _ = torch.__version__
        return True
    except Exception as e:
        import traceback

        err = f"is_torch_available exception: {e}\n{traceback.format_exc()}"
        logger.error(err)
        try:
            log_p = Path.home() / ".cache" / "devoice" / "torch_error.log"
            log_p.parent.mkdir(parents=True, exist_ok=True)
            log_p.write_text(err, encoding="utf-8")
        except Exception:
            pass
        return False


def is_cuda_available() -> bool:
    """Check if CUDA acceleration is functional in the active PyTorch environment."""
    setup_runtime_environment()
    try:
        import torch  # type: ignore

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def detect_system_hardware() -> dict[str, str | bool]:
    """Detect GPU hardware and return user-friendly diagnostic info."""
    info: dict[str, str | bool] = {
        "has_nvidia": False,
        "gpu_name": "Processeur (CPU)",
        "recommended_flavor": "cpu",
        "details": "",
    }

    if sys.platform == "win32":
        try:
            # Query Windows WMI / CIM for Nvidia display controllers
            out = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                clean = line.strip()
                if "nvidia" in clean.lower() or "geforce" in clean.lower() or "rtx" in clean.lower() or "gtx" in clean.lower():
                    info["has_nvidia"] = True
                    info["gpu_name"] = clean
                    info["recommended_flavor"] = "cuda"
                    info["details"] = "Accélération matérielle NVIDIA détectée"
                    return info
        except Exception:
            pass

    info["details"] = "Aucun GPU NVIDIA détecté — exécution sur processeur"
    return info


def download_file_with_progress(
    url: str,
    dest_path: Path,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_flag: Callable[[], bool] | None = None,
) -> Path:
    """Download a file with high-speed chunking and progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Devoice-Installer/1.0"},
    )

    with urllib.request.urlopen(req, timeout=60) as response, open(temp_path, "wb") as out_file:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1 MB buffer

        while True:
            if cancel_flag and cancel_flag():
                out_file.close()
                if temp_path.exists():
                    temp_path.unlink()
                raise InterruptedError("Téléchargement annulé par l'utilisateur.")

            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)

            if total_size > 0 and progress_callback:
                pct = int((downloaded / total_size) * 100)
                mb_curr = downloaded / (1024 * 1024)
                mb_tot = total_size / (1024 * 1024)
                progress_callback(pct, f"Téléchargement : {mb_curr:.1f} Mo / {mb_tot:.1f} Mo ({pct}%)")

    if temp_path.exists():
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)

    return dest_path


def extract_zip_archive(
    zip_path: Path,
    target_dir: Path,
    progress_callback: Callable[[int, str], None] | None = None,
) -> None:
    """Extract a ZIP archive into the destination directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()
        total = len(members)
        for idx, member in enumerate(members):
            zf.extract(member, target_dir)
            if progress_callback and total > 0 and idx % 20 == 0:
                pct = int((idx / total) * 100)
                progress_callback(pct, f"Extraction du moteur : {pct}%")

    if progress_callback:
        progress_callback(100, "Extraction terminée.")
