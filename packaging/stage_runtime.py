"""Script to assemble the optimized AI runtime bundle for Devoice All-in-One installer.

Copies torch (CUDA 12.1), onnxruntime-gpu, audio_separator and their dependencies
into dist/runtime, stripping out unused static .lib files, test folders, and C++ headers
to minimize installer size while guaranteeing 100% functionality.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SITE_PACKAGES = ROOT_DIR / "venv" / "Lib" / "site-packages"
DEST_RUNTIME = ROOT_DIR / "dist" / "runtime"

PACKAGES = [
    "torch",
    "torchgen",
    "functorch",
    "torchaudio",
    "audio_separator",
    "onnxruntime",
    "rotary_embedding_torch",
    "einops",
    "ml_collections",
    "beartype",
    "absl",
    "filelock",
    "mpmath",
    "sympy",
    "contextlib2",
    "progress",
    "audioread",
]

SINGLE_FILES = [
    "typing_extensions.py",
    "pickletools.py",
    "dis.py",
    "opcode.py",
    "pdb.py",
    "bdb.py",
    "cmd.py",
    "code.py",
    "codeop.py",
    "doctest.py",
    "difflib.py",
    "tarfile.py",
    "uuid.py",
    "quopri.py",
    "webbrowser.py",
]

# Patterns to skip to keep the installer lightweight without breaking execution
IGNORE_EXTENSIONS = {".lib", ".pdb", ".h", ".hpp", ".c", ".cpp"}
IGNORE_DIRS = {"tests", "test", "__pycache__", "include"}


def copy_with_filters(src: Path, dst: Path) -> None:
    if src.is_file():
        if src.suffix.lower() not in IGNORE_EXTENSIONS:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return

    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        # Exclude blacklisted directories
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]

        rel_root = Path(root).relative_to(src)
        target_dir = dst / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            f_path = Path(file)
            if f_path.suffix.lower() in IGNORE_EXTENSIONS:
                continue
            src_file = Path(root) / file
            dst_file = target_dir / file
            shutil.copy2(src_file, dst_file)


def main() -> None:
    print(f"Staging runtime from: {SITE_PACKAGES}")
    print(f"Target destination:  {DEST_RUNTIME}")

    if DEST_RUNTIME.exists():
        print("Cleaning previous dist/runtime...")
        shutil.rmtree(DEST_RUNTIME)
    DEST_RUNTIME.mkdir(parents=True, exist_ok=True)

    for pkg in PACKAGES:
        src = SITE_PACKAGES / pkg
        if src.exists():
            print(f"  Copying {pkg}...")
            copy_with_filters(src, DEST_RUNTIME / pkg)
        else:
            print(f"  WARNING: {pkg} not found in site-packages!")

    py_stdlib = Path(os.path.dirname(os.__file__))

    # Copy stdlib packages required by torch but omitted by PyInstaller
    for std_pkg in ["unittest"]:
        src = py_stdlib / std_pkg
        if src.exists():
            print(f"  Copying stdlib package {std_pkg}...")
            copy_with_filters(src, DEST_RUNTIME / std_pkg)

    for sfile in SINGLE_FILES:
        src = SITE_PACKAGES / sfile
        if not src.exists():
            src = py_stdlib / sfile
        if src.exists():
            print(f"  Copying {sfile}...")
            shutil.copy2(src, DEST_RUNTIME / sfile)
        else:
            print(f"  WARNING: {sfile} not found in site-packages or stdlib!")

    # Calculate total size
    total_bytes = sum(f.stat().st_size for f in DEST_RUNTIME.rglob("*") if f.is_file())
    total_mb = total_bytes / (1024 * 1024)
    print(f"\nRuntime staging complete! Total uncompressed size: {total_mb:.1f} MB")


if __name__ == "__main__":
    main()
