"""Drag-and-drop zone widget for importing audio files."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)


#: Audio file extensions accepted by the application.
SUPPORTED_FORMATS: set[str] = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".opus",
}


class DropZone(QWidget):
    """A drag-and-drop area that accepts audio files.

    Users can either drag files onto this widget or click it to open
    a file-browser dialog. Accepted files are emitted via the
    :pyqtSignal:`files_dropped` signal as a list of :class:`Path` objects.
    """

    files_dropped: pyqtSignal = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # --- layout ---
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("🎵")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        layout.addWidget(icon_label)

        text_label = QLabel("Glisse tes fichiers audio ici\nou clique pour parcourir")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(
            "color: #8888aa; font-size: 13px; background: transparent; border: none;"
        )
        layout.addWidget(text_label)

    # ------------------------------------------------------------------
    # Drag-and-drop events
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        """Accept the drag if it carries URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QWidget#DropZone { border-color: #7c3aed; background-color: #1e1e38; }")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        """Reset styling when the drag leaves the widget."""
        self.setStyleSheet("")
        event.accept()

    def dropEvent(self, event) -> None:  # noqa: N802
        """Filter dropped files by supported format and emit them."""
        self.setStyleSheet("")
        valid_files: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_FORMATS:
                valid_files.append(path)
        if valid_files:
            self.files_dropped.emit(valid_files)
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Click-to-browse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Open a file dialog to let the user pick audio files."""
        extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_FORMATS))
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers audio",
            "",
            f"Fichiers audio ({extensions});;Tous les fichiers (*)",
        )
        if file_paths:
            self.files_dropped.emit([Path(p) for p in file_paths])
