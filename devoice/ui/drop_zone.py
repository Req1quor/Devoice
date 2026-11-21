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
        self.setMinimumHeight(155)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self._icon_label = QLabel("◈")
        self._icon_label.setObjectName("DropZoneIcon")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 32px; font-weight: 300; color: #a1a1aa;")

        self._text_label = QLabel("DÉPOSEZ UN FICHIER AUDIO\nou cliquez pour parcourir")
        self._text_label.setObjectName("DropZoneLabel")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setWordWrap(True)

        self._sub_label = QLabel("WAV · MP3 · FLAC · M4A · AIFF · OGG")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setWordWrap(True)
        self._sub_label.setStyleSheet("font-size: 11px; color: #52525b; letter-spacing: 1px;")

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._sub_label)

    def set_loaded_file(self, path: Path | None) -> None:
        """Update drop zone appearance when a file is loaded."""
        if path is not None:
            self._icon_label.setText("🎵")
            self._icon_label.setStyleSheet("font-size: 28px; color: #ffffff;")
            self._text_label.setText(path.name)
            self._text_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
            self._sub_label.setText("Fichier chargé · Cliquez ou glissez pour remplacer")
            self._sub_label.setStyleSheet("font-size: 11px; color: #4ade80;")
            self.setProperty("loaded", "true")
        else:
            self._icon_label.setText("◈")
            self._icon_label.setStyleSheet("font-size: 32px; font-weight: 300; color: #a1a1aa;")
            self._text_label.setText("DÉPOSEZ UN FICHIER AUDIO\nou cliquer pour parcourir")
            self._text_label.setStyleSheet("")
            self._sub_label.setText("WAV · MP3 · FLAC · M4A · AIFF · OGG")
            self._sub_label.setStyleSheet("font-size: 11px; color: #52525b; letter-spacing: 1px;")
            self.setProperty("loaded", "false")
        self.setStyle(self.style())

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
