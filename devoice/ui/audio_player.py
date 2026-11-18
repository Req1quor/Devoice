"""Audio preview player widget for comparing vocal and instrumental stems."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class AudioPreviewPlayer(QWidget):
    """Inline player to preview separated vocal and instrumental tracks.

    Provides two source-selector buttons ("Voix" and "Instru"), a play/pause
    toggle and a seek slider.  Hidden by default; call :meth:`set_results` to
    populate paths and show the widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)

        self._vocals_path: Path | None = None
        self._instru_path: Path | None = None

        # --- media backend ---
        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.8)

        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

        # --- controls ---
        self._btn_vocals = QPushButton("🎤 Voix")
        self._btn_instru = QPushButton("🎹 Instru")
        self._btn_play = QPushButton("▶")

        self._btn_vocals.clicked.connect(self._load_vocals)
        self._btn_instru.clicked.connect(self._load_instru)
        self._btn_play.clicked.connect(self._toggle_play)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderMoved.connect(self._seek)

        # --- layout ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self._btn_vocals)
        btn_layout.addWidget(self._btn_instru)
        btn_layout.addWidget(self._btn_play)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 0)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self._slider)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_results(self, vocals_path: Path, instru_path: Path) -> None:
        """Set the paths to the separated stems and auto-load the vocals.

        Args:
            vocals_path: Path to the extracted vocal track.
            instru_path: Path to the instrumental (accompaniment) track.
        """
        self._vocals_path = vocals_path
        self._instru_path = instru_path
        self._load_vocals()
        self.setVisible(True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_vocals(self) -> None:
        """Load the vocals file into the player."""
        if self._vocals_path and self._vocals_path.exists():
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(str(self._vocals_path)))
            self._btn_play.setText("▶")

    def _load_instru(self) -> None:
        """Load the instrumental file into the player."""
        if self._instru_path and self._instru_path.exists():
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(str(self._instru_path)))
            self._btn_play.setText("▶")

    def _toggle_play(self) -> None:
        """Toggle between play and pause states."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._btn_play.setText("▶")
        else:
            self._player.play()
            self._btn_play.setText("⏸")

    def _seek(self, position: int) -> None:
        """Seek the player to *position* milliseconds."""
        self._player.setPosition(position)

    def _on_position_changed(self, position: int) -> None:
        """Sync the slider with the current playback position."""
        if not self._slider.isSliderDown():
            self._slider.setValue(position)

    def _on_duration_changed(self, duration: int) -> None:
        """Update slider range when the loaded media changes."""
        self._slider.setRange(0, duration)
