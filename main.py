"""Devoice entry point."""

import sys

# Ensure static ffmpeg is on PATH immediately on launch
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from devoice.ui.main_window import MainWindow
from devoice.ui.styles import DARK_THEME


def main():
    if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    app = QApplication(sys.argv)
    app.setApplicationName("Devoice")
    app.setStyleSheet(DARK_THEME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
