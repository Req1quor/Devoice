# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Devoice desktop application."""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all dynamic libraries, hidden imports, and assets for heavy dependencies
packages_to_collect = [
    "torch",
    "torchaudio",
    "demucs",
    "PyQt6",
    "audio_separator",
    "onnxruntime",
    "scipy",
    "librosa",
    "soundfile",
    "pydub",
    "yt_dlp",
    "static_ffmpeg",
]

binaries = []
datas = [
    ("devoice/assets", "devoice/assets"),
]
collected_hiddenimports = []

for pkg in packages_to_collect:
    try:
        pkg_data = collect_all(pkg)
        binaries.extend(pkg_data.get("binaries", []))
        datas.extend(pkg_data.get("datas", []))
        collected_hiddenimports.extend(pkg_data.get("hiddenimports", []))
    except Exception:
        pass

# Static FFmpeg binary resolution and collection
try:
    import static_ffmpeg._add_paths as sff
    ffmpeg_exe, ffprobe_exe = sff.get_or_fetch_platform_executables_else_raise()
    if ffmpeg_exe and Path(ffmpeg_exe).exists():
        binaries.append((str(ffmpeg_exe), "."))
    if ffprobe_exe and Path(ffprobe_exe).exists():
        binaries.append((str(ffprobe_exe), "."))
except Exception:
    pass

# Include local ffmpeg binaries if placed in packaging/ or project root
for p in [
    Path("ffmpeg.exe"),
    Path("ffprobe.exe"),
    Path("packaging/ffmpeg.exe"),
    Path("packaging/ffprobe.exe"),
]:
    if p.exists():
        binaries.append((str(p), "."))

# Explicit hidden imports to guarantee all dynamic imports are resolved
hiddenimports = list(set([
    "torch",
    "torchaudio",
    "demucs",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtMultimedia",
    "soundfile",
    "numpy",
    "audio_separator",
    "onnxruntime",
    "scipy",
    "scipy.signal",
    "scipy.ndimage",
    "scipy.special",
    "librosa",
    "pydub",
    "yt_dlp",
    "static_ffmpeg",
] + collected_hiddenimports))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Devoice",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX often causes issues with large PyTorch DLLs
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Devoice",
)
