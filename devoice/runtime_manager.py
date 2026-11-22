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


def get_runtime_dir() -> Path:
    """Return the persistent directory where the AI audio runtime is installed."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Devoice" / "runtime"
    return Path.home() / ".cache" / "devoice" / "runtime"


def setup_runtime_environment(runtime_dir: Path | None = None) -> bool:
    """Inject runtime directory into sys.path and Windows DLL search path.

    Must be called before importing torch or heavy ML dependencies.
    """
    if runtime_dir is None:
        runtime_dir = get_runtime_dir()

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
    except Exception:
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
