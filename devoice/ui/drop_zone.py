"""Minimalist drag & drop widget for Devoice."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget

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


class DropZone(QWidget):
    """Clean minimalist drop target for audio files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(150)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        self._icon_label = QLabel("+")
        self._icon_label.setObjectName("DropZoneIcon")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 28px; font-weight: 300; color: #71717a;")

        self._text_label = QLabel("GLISSER UN FICHIER AUDIO\nou cliquer pour parcourir")
        self._text_label.setObjectName("DropZoneLabel")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sub_label = QLabel("WAV · MP3 · FLAC · OGG · M4A")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setStyleSheet("font-size: 10px; color: #52525b; letter-spacing: 1px;")

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._sub_label)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("#DropZone { border-color: #ffffff; background-color: #141418; }")
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
