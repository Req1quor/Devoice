"""Devoice entry point."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

# Required for frozen Windows multiprocessing support
multiprocessing.freeze_support()

# Ensure static ffmpeg is on PATH immediately on launch
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from devoice.ui.main_window import MainWindow
from devoice.ui.splash_screen import StudioSplashScreen
from devoice.ui.styles import DARK_THEME


def main() -> None:
    if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    app = QApplication(sys.argv)
    app.setApplicationName("Devoice")
    app.setStyleSheet(DARK_THEME)

    # Set application icon (window frame, alt-tab, and taskbar)
    icon_candidates = [
        Path(__file__).resolve().parent / "devoice" / "assets" / "icon.png",
        Path(__file__).resolve().parent / "packaging" / "icon.ico",
        Path(sys.executable).parent / "_internal" / "devoice" / "assets" / "icon.png",
    ]
    for icp in icon_candidates:
        if icp.exists():
            app.setWindowIcon(QIcon(str(icp)))
            break

    window = MainWindow()

    # Studio animated splash screen on launch
    splash = StudioSplashScreen()
    splash.splash_finished.connect(window.show)
    splash.start_animation()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
