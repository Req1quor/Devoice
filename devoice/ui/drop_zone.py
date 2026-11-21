"""Monospace ASCII / Dither drag & drop widget for Devoice."""

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
    """ASCII / Dither hardware styled drop target for audio files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(140)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self._banner_label = QLabel("[ ░░░▒▒▓▓ DÉPOSER LE FICHIER AUDIO ICI ▓▓▒▒░░░ ]")
        self._banner_label.setObjectName("DropZoneIcon")
        self._banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._banner_label.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 13px; font-weight: 700; color: #a1a1aa; letter-spacing: 1px;"
        )

        self._text_label = QLabel(">> OU CLIQUER POUR PARCOURIR LE DISQUE")
        self._text_label.setObjectName("DropZoneLabel")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 12px; font-weight: 700; color: #ffffff; letter-spacing: 0.8px;"
        )

        self._sub_label = QLabel("FORMATS: WAV · MP3 · FLAC · M4A · AIFF · OGG · OPUS")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setWordWrap(True)
        self._sub_label.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 10px; color: #52525b; letter-spacing: 1px;"
        )

        layout.addWidget(self._banner_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._sub_label)

    def set_loaded_file(self, path: Path | None) -> None:
        """Update drop zone appearance when a file is loaded."""
        if path is not None:
            self._banner_label.setText("[+] FICHIER SOURCE CHARGÉ")
            self._banner_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; color: #22c55e; letter-spacing: 1px;"
            )
            self._text_label.setText(f">> {path.name.upper()}")
            self._text_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 13px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;"
            )
            self._sub_label.setText("STATUS: PRÊT POUR EXTRACTION // CLIQUER OU GLISSER POUR REMPLACER")
            self._sub_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; color: #71717a; letter-spacing: 0.5px;"
            )
            self.setProperty("loaded", "true")
        else:
            self._banner_label.setText("[ ░░░▒▒▓▓ DÉPOSER LE FICHIER AUDIO ICI ▓▓▒▒░░░ ]")
            self._banner_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 13px; font-weight: 700; color: #a1a1aa; letter-spacing: 1px;"
            )
            self._text_label.setText(">> OU CLIQUER POUR PARCOURIR LE DISQUE")
            self._text_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 12px; font-weight: 700; color: #ffffff; letter-spacing: 0.8px;"
            )
            self._sub_label.setText("FORMATS: WAV · MP3 · FLAC · M4A · AIFF · OGG · OPUS")
            self._sub_label.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; color: #52525b; letter-spacing: 1px;"
            )
            self.setProperty("loaded", "false")
        self.setStyle(self.style())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("#DropZone { border: 1px solid #ffffff; background-color: #121217; }")
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
