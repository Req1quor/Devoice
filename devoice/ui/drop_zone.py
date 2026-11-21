"""Clean minimalist drag & drop widget for Devoice."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout, QWidget

SUPPORTED_FORMATS = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".opus",
    ".webm",
}


class DropZone(QFrame):
    """Minimalist audio drop zone with consistent layout."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self._title_label = QLabel("Déposer un fichier audio ici")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f3f9;")

        self._subtitle_label = QLabel("ou cliquer pour parcourir")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet("font-size: 12px; color: #8a90a4;")

        self._formats_label = QLabel("WAV · MP3 · FLAC · M4A · AIFF · OGG")
        self._formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._formats_label.setStyleSheet("font-size: 11px; color: #555c70;")

        layout.addWidget(self._title_label)
        layout.addWidget(self._subtitle_label)
        layout.addWidget(self._formats_label)

    def set_loaded_file(self, path: Path | None) -> None:
        """Update appearance when a file is loaded."""
        if path is not None:
            self._title_label.setText(path.name)
            self._title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff;")
            self._subtitle_label.setText("Fichier prêt · Cliquer pour remplacer")
            self._subtitle_label.setStyleSheet("font-size: 11px; color: #3b82f6;")
            self._formats_label.setVisible(False)
            self.setProperty("loaded", "true")
        else:
            self._title_label.setText("Déposer un fichier audio ici")
            self._title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f3f9;")
            self._subtitle_label.setText("ou cliquer pour parcourir")
            self._subtitle_label.setStyleSheet("font-size: 12px; color: #8a90a4;")
            self._formats_label.setVisible(True)
            self.setProperty("loaded", "false")
        self.setStyle(self.style())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("#DropZone { border-color: #3b82f6; background-color: #141722; }")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setStyleSheet("")

    def dropEvent(self, event) -> None:
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        audio_paths: List[Path] = []
        for url in urls:
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_FORMATS:
                audio_paths.append(path)
        if audio_paths:
            self.files_dropped.emit(audio_paths)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            formats_filter = "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma *.aiff *.opus *.webm)"
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Sélectionner des fichiers audio",
                "",
                formats_filter,
            )
            if files:
                self.files_dropped.emit([Path(f) for f in files])
