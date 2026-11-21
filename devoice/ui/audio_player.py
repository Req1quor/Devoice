"""High-end studio minimalist audio player in pure Noir & Blanc."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class AudioPreviewPlayer(QWidget):
    """Studio-grade minimalist player in Noir & Blanc."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)

        self._original_path: Path | None = None
        self._vocals_path: Path | None = None
        self._instru_path: Path | None = None
        self._active_stem: str = "vocals"

        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.85)

        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

        self._build_ui()

    def _build_ui(self) -> None:
        card = QFrame(self)
        card.setObjectName("PlayerCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        # Header row: Track stem & time
        top_row = QHBoxLayout()
        self._label_track = QLabel("LECTURE : VOIX")
        self._label_track.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #71717a; letter-spacing: 0.8px;"
        )

        self._label_time = QLabel("00:00 / 00:00")
        self._label_time.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600; color: #ffffff;"
        )

        top_row.addWidget(self._label_track)
        top_row.addStretch()
        top_row.addWidget(self._label_time)
        card_layout.addLayout(top_row)

        # Scrubber Slider (Full width)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._slider.sliderMoved.connect(self._seek)
        card_layout.addWidget(self._slider)

        # Controls row: Play button + Stem selectors
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self._btn_play = QPushButton("Play")
        self._btn_play.setObjectName("PlayButton")
        self._btn_play.setFixedWidth(70)
        self._btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_play.clicked.connect(self._toggle_play)
        controls_row.addWidget(self._btn_play)

        controls_row.addSpacing(6)

        self._btn_vocals = QPushButton("Voix")
        self._btn_vocals.setObjectName("StemActive")
        self._btn_vocals.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_vocals.clicked.connect(lambda: self._switch_stem("vocals"))
        controls_row.addWidget(self._btn_vocals)

        self._btn_instru = QPushButton("Instrumentale")
        self._btn_instru.setObjectName("StemInactive")
        self._btn_instru.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_instru.clicked.connect(lambda: self._switch_stem("instru"))
        controls_row.addWidget(self._btn_instru)

        self._btn_orig = QPushButton("Original")
        self._btn_orig.setObjectName("StemInactive")
        self._btn_orig.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_orig.clicked.connect(lambda: self._switch_stem("original"))
        controls_row.addWidget(self._btn_orig)

        controls_row.addStretch()
        card_layout.addLayout(controls_row)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

    def set_results(
        self,
        vocals_path: Path | str,
        instru_path: Path | str,
        original_path: Path | str | None = None,
    ) -> None:
        self._vocals_path = Path(vocals_path) if vocals_path else None
        self._instru_path = Path(instru_path) if instru_path else None
        self._original_path = Path(original_path) if original_path else None

        self._btn_orig.setVisible(self._original_path is not None and self._original_path.exists())

        self._active_stem = "vocals"
        self._apply_stem_source(seek_to_zero=True)
        self.setVisible(True)

    def update_vocals(self, new_vocals_path: Path | str) -> None:
        """Seamlessly reload media source via setSource, preserving current position and playback state."""
        self._vocals_path = Path(new_vocals_path)
        if self._active_stem == "vocals" and self._vocals_path.exists():
            was_playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            current_pos = self._player.position()

            self._player.setSource(QUrl.fromLocalFile(str(self._vocals_path)))
            if current_pos > 0:
                self._player.setPosition(current_pos)

            if was_playing:
                self._player.play()
                self._btn_play.setText("Pause")

    def _switch_stem(self, target_stem: str) -> None:
        if target_stem == self._active_stem:
            return

        self._active_stem = target_stem
        self._apply_stem_source(seek_to_zero=False)

    def _apply_stem_source(self, seek_to_zero: bool = False) -> None:
        target_path: Path | None = None
        if self._active_stem == "original":
            target_path = self._original_path
            title = "LECTURE : MIX ORIGINAL"
        elif self._active_stem == "vocals":
            target_path = self._vocals_path
            title = "LECTURE : VOIX ISOLÉE"
        else:
            target_path = self._instru_path
            title = "LECTURE : INSTRUMENTALE"

        if not target_path or not target_path.exists():
            return

        self._label_track.setText(title)

        self._btn_vocals.setObjectName("StemActive" if self._active_stem == "vocals" else "StemInactive")
        self._btn_instru.setObjectName("StemActive" if self._active_stem == "instru" else "StemInactive")
        self._btn_orig.setObjectName("StemActive" if self._active_stem == "original" else "StemInactive")

        for b in (self._btn_vocals, self._btn_instru, self._btn_orig):
            b.setStyle(b.style())

        was_playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        current_pos = 0 if seek_to_zero else self._player.position()

        self._player.setSource(QUrl.fromLocalFile(str(target_path)))
        if current_pos > 0:
            self._player.setPosition(current_pos)

        if was_playing:
            self._player.play()
            self._btn_play.setText("Pause")

    def _toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._btn_play.setText("Play")
        else:
            self._player.play()
            self._btn_play.setText("Pause")

    def _seek(self, position: int) -> None:
        self._player.setPosition(position)

    def _on_position_changed(self, position: int) -> None:
        if not self._slider.isSliderDown():
            self._slider.setValue(position)
        self._update_time_label(position, self._player.duration())

    def _on_duration_changed(self, duration: int) -> None:
        self._slider.setRange(0, duration)
        self._update_time_label(self._player.position(), duration)

    def _update_time_label(self, pos_ms: int, dur_ms: int) -> None:
        pos_s = pos_ms // 1000
        dur_s = dur_ms // 1000
        self._label_time.setText(f"{pos_s // 60:02d}:{pos_s % 60:02d} / {dur_s // 60:02d}:{dur_s % 60:02d}")
