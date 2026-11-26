"""Devoice entry point with dynamic runtime support."""

from __future__ import annotations

import multiprocessing
import os
import sys
import traceback
from pathlib import Path

# Required for frozen Windows multiprocessing support
multiprocessing.freeze_support()

# Ensure stdout/stderr are not None in windowed PyInstaller mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Ensure static ffmpeg is on PATH immediately on launch
from devoice.runtime_manager import (
    ensure_ffmpeg_paths,
    is_torch_available,
    setup_runtime_environment,
)

ensure_ffmpeg_paths()
setup_runtime_environment()

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from devoice.ui.styles import DARK_THEME


def main() -> None:
    try:
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        app = QApplication(sys.argv)
        app.setApplicationName("Devoice")
        app.setStyleSheet(DARK_THEME)
        app.setQuitOnLastWindowClosed(False)

        # Retain root window reference to prevent Python GC from releasing it
        app.main_window = None

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

        # If PyTorch runtime is already present, launch with studio splash screen
        if is_torch_available():
            from devoice.ui.main_window import MainWindow
            from devoice.ui.splash_screen import StudioSplashScreen

            window = MainWindow()
            app.main_window = window

            splash = StudioSplashScreen()
            app.splash = splash

            def _on_splash_done():
                window.show()
                window.raise_()
                window.activateWindow()
                app.setQuitOnLastWindowClosed(True)

            splash.splash_finished.connect(_on_splash_done)
            splash.start_animation()
        else:
            # First launch onboarding: download the appropriate runtime
            from devoice.ui.runtime_dialog import RuntimeSetupDialog

            dialog = RuntimeSetupDialog()
            app.dialog = dialog

            def _on_runtime_ready():
                from devoice.ui.main_window import MainWindow

                win = MainWindow()
                app.main_window = win
                win.show()
                win.raise_()
                win.activateWindow()
                app.setQuitOnLastWindowClosed(True)

            dialog.runtime_ready.connect(_on_runtime_ready)
            dialog.show()

        sys.exit(app.exec())

    except Exception as exc:
        err_msg = traceback.format_exc()
        try:
            log_path = Path.home() / ".cache" / "devoice" / "crash.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(err_msg, encoding="utf-8")
        except Exception:
            pass

        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                f"Une erreur est survenue au démarrage de Devoice :\n\n{exc}\n\nConsultez crash.log pour plus de détails.",
                "Devoice — Erreur de Démarrage",
                0x10,
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
