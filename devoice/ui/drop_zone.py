"""Studio-grade audio cartridge drag & drop widget for Devoice."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout, QWidget

from devoice.youtube import is_youtube_url

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
    """Studio-grade audio drop cartridge with dynamic QSS properties."""

    files_dropped = pyqtSignal(list)
    youtube_url_dropped = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(112)

        self.setProperty("dragOver", False)
        self.setProperty("loaded", "false")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(5)

        self._title_label = QLabel("Déposer un fichier audio ici")
        self._title_label.setObjectName("DropZoneTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setWordWrap(True)

        self._subtitle_label = QLabel("ou cliquer pour parcourir")
        self._subtitle_label.setObjectName("DropZoneSubtitle")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._formats_label = QLabel("WAV · MP3 · FLAC · M4A · AIFF · OGG")
        self._formats_label.setObjectName("DropZoneFormats")
        self._formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._title_label)
        layout.addWidget(self._subtitle_label)
        layout.addWidget(self._formats_label)

    def set_loaded_file(self, path: Path | None) -> None:
        """Update appearance when a file is loaded."""
        if path is not None:
            self._title_label.setText(path.name)
            self._subtitle_label.setText("Fichier prêt · Cliquer pour remplacer")
            self._formats_label.setVisible(False)
            self.setProperty("loaded", "true")
        else:
            self._title_label.setText("Déposer un fichier audio ici")
            self._subtitle_label.setText("ou cliquer pour parcourir")
            self._formats_label.setVisible(True)
            self.setProperty("loaded", "false")
        self.setStyle(self.style())

    def set_downloading(
        self,
        title: str = "Téléchargement YouTube…",
        subtitle: str = "Récupération audio en cours…",
    ) -> None:
        """Update appearance during YouTube download."""
        self._title_label.setText(title)
        self._subtitle_label.setText(subtitle)
        self._formats_label.setVisible(False)
        self.setProperty("loaded", "true")
        self.setStyle(self.style())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self.setProperty("dragOver", True)
            self.setStyle(self.style())
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragOver", False)
        self.setStyle(self.style())

    def dropEvent(self, event) -> None:
        self.setProperty("dragOver", False)
        self.setStyle(self.style())

        # 1. Check for dropped YouTube URL
        if event.mimeData().hasText():
            text = event.mimeData().text().strip()
            if is_youtube_url(text):
                self.youtube_url_dropped.emit(text)
                return

        urls = event.mimeData().urls()
        for url in urls:
            raw_url = url.toString()
            if is_youtube_url(raw_url):
                self.youtube_url_dropped.emit(raw_url)
                return

        # 2. Check for local audio files
        audio_paths: list[Path] = []
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
