"""Devoice entry point with dynamic runtime support."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

# Required for frozen Windows multiprocessing support
multiprocessing.freeze_support()

# Register dynamic runtime directory if present
from devoice.runtime_manager import is_torch_available, setup_runtime_environment

setup_runtime_environment()

# Ensure static ffmpeg is on PATH immediately on launch
try:
    if getattr(sys, "frozen", False):
        meipass_ffmpeg = Path(sys._MEIPASS) / "static_ffmpeg" / "bin" / "win32"
        if meipass_ffmpeg.exists():
            os.environ["PATH"] = str(meipass_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
    import static_ffmpeg
    static_ffmpeg.add_paths(weak=True)
except Exception:
    pass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

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

    # If PyTorch runtime is already present, launch directly with studio splash
    if is_torch_available():
        from devoice.ui.main_window import MainWindow
        from devoice.ui.splash_screen import StudioSplashScreen

        window = MainWindow()
        splash = StudioSplashScreen()
        splash.splash_finished.connect(window.show)
        splash.start_animation()
    else:
        # First launch onboarding: download the appropriate runtime
        from devoice.ui.runtime_dialog import RuntimeSetupDialog

        dialog = RuntimeSetupDialog()

        def _on_runtime_ready():
            from devoice.ui.main_window import MainWindow

            win = MainWindow()
            win.show()

        dialog.runtime_ready.connect(_on_runtime_ready)
        dialog.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
