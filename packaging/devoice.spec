# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Devoice desktop application (Web / Dynamic Runtime Edition).

Produces an ultra-lightweight (< 80 MB) standalone application bundle.
PyTorch and heavy CUDA weights are loaded dynamically on demand via RuntimeManager.
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT_DIR = Path(SPECPATH).resolve().parent

block_cipher = None

# Collect only GUI, DSP, audio codecs, and download tools
packages_to_collect = [
    "PyQt6",
    "scipy",
    "librosa",
    "soundfile",
    "pydub",
    "yt_dlp",
    "static_ffmpeg",
]

binaries = []
datas = [
    (str(ROOT_DIR / "devoice" / "assets"), "devoice/assets"),
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

# Static FFmpeg binary resolution and collection (single exact destination)
ffmpeg_found = False
try:
    import static_ffmpeg._add_paths as sff
    ffmpeg_exe, ffprobe_exe = sff.get_or_fetch_platform_executables_else_raise()
    if ffmpeg_exe and Path(ffmpeg_exe).exists():
        binaries.append((str(ffmpeg_exe), "."))
        ffmpeg_found = True
    if ffprobe_exe and Path(ffprobe_exe).exists():
        binaries.append((str(ffprobe_exe), "."))
except Exception:
    pass

if not ffmpeg_found:
    for p in [
        ROOT_DIR / "venv" / "Lib" / "site-packages" / "static_ffmpeg" / "bin" / "win32" / "ffmpeg.exe",
        ROOT_DIR / "venv" / "Lib" / "site-packages" / "static_ffmpeg" / "bin" / "win32" / "ffprobe.exe",
        ROOT_DIR / "ffmpeg.exe",
        ROOT_DIR / "ffprobe.exe",
        ROOT_DIR / "packaging" / "ffmpeg.exe",
        ROOT_DIR / "packaging" / "ffprobe.exe",
    ]:
        if p.exists():
            binaries.append((str(p), "."))

# Explicit hidden imports for the core desktop GUI and DSP engine
hiddenimports = list(set([
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtMultimedia",
    "soundfile",
    "numpy",
    "unittest",
    "pickletools",
    "dis",
    "opcode",
    "pdb",
    "bdb",
    "cmd",
    "code",
    "codeop",
    "doctest",
    "difflib",
    "tarfile",
    "uuid",
    "quopri",
    "scipy",
    "scipy.signal",
    "scipy.linalg",
    "scipy.ndimage",
    "scipy.special",
    "librosa",
    "pydub",
    "yt_dlp",
    "static_ffmpeg",
] + collected_hiddenimports))

a = Analysis(
    [str(ROOT_DIR / "main.py")],
    pathex=[str(ROOT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy machine learning packages excluded to keep installer under 80 MB
        "torch",
        "torchaudio",
        "demucs",
        "audio_separator",
        "onnxruntime",
        "onnx",
        "tkinter",
        "matplotlib",
        "pytest",
        "IPython",
        "jupyter",
        "setuptools",
        "wheel",
        "pip",
    ],
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
    upx=False,
    console=False,
    icon=str(ROOT_DIR / "packaging" / "icon.ico"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Filter out redundant binaries, debug symbols, and test assets
filtered_binaries = []
excluded_binaries_set = {
    "opengl32sw.dll",             # 21 MB software fallback OpenGL (GPU native used)
    "Qt6Pdf.dll",                 # 5.5 MB unused PDF engine in PyQt6
}

for item in a.binaries:
    dest_name = Path(item[0]).name
    if dest_name in excluded_binaries_set:
        continue
    filtered_binaries.append(item)

# Filter out test suites, documentation, and cached bytecode in datas
filtered_datas = []
for item in a.datas:
    source_path = item[0]
    target_path = item[1]
    if "win32.zip" in target_path.lower():
        continue
    if any(k in target_path.lower() for k in ("test", "testing", "benchmarks", "__pycache__")):
        continue
    filtered_datas.append(item)

coll = COLLECT(
    exe,
    filtered_binaries,
    a.zipfiles,
    filtered_datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Devoice",
)
