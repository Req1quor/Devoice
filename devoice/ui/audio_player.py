"""Synchronized modern audio preview player for Original, Vocals, and Instrumental."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

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
    """Synchronized A/B/C player for instant stem comparison."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)

        self._original_path: Optional[Path] = None
        self._vocals_path: Optional[Path] = None
        self._instru_path: Optional[Path] = None
        self._active_stem: str = "vocals"

        # Media Backend
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

        # Header with active track label and time
        top_row = QHBoxLayout()
        self._label_track = QLabel("PRÉÉCOUTE DES RÉSULTATS")
        self._label_track.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")

        self._label_time = QLabel("00:00 / 00:00")
        self._label_time.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b;")

        top_row.addWidget(self._label_track)
        top_row.addStretch()
        top_row.addWidget(self._label_time)
        card_layout.addLayout(top_row)

        # Controls row: Play button + Stem selectors
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self._btn_play = QPushButton("Lecture")
        self._btn_play.setFixedWidth(80)
        self._btn_play.setStyleSheet(
            "background-color: #3b82f6; color: #ffffff; font-weight: 700; border: none;"
        )
        self._btn_play.clicked.connect(self._toggle_play)
        controls_row.addWidget(self._btn_play)

        controls_row.addSpacing(4)

        self._btn_vocals = QPushButton("Voix isolée")
        self._btn_vocals.clicked.connect(lambda: self._switch_stem("vocals"))
        controls_row.addWidget(self._btn_vocals)

        self._btn_instru = QPushButton("Instrumentale")
        self._btn_instru.clicked.connect(lambda: self._switch_stem("instru"))
        controls_row.addWidget(self._btn_instru)

        self._btn_orig = QPushButton("Mix original")
        self._btn_orig.clicked.connect(lambda: self._switch_stem("original"))
        controls_row.addWidget(self._btn_orig)

        controls_row.addStretch()
        card_layout.addLayout(controls_row)

        # Scrubber Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderMoved.connect(self._seek)
        card_layout.addWidget(self._slider)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

    def set_results(
        self,
        vocals_path: Path | str,
        instru_path: Path | str,
        original_path: Optional[Path | str] = None,
    ) -> None:
        """Set paths for vocals, instrumental, and optional original mix."""
        self._vocals_path = Path(vocals_path) if vocals_path else None
        self._instru_path = Path(instru_path) if instru_path else None
        self._original_path = Path(original_path) if original_path else None

        self._btn_orig.setVisible(self._original_path is not None and self._original_path.exists())

        self._active_stem = "vocals"
        self._apply_stem_source(seek_to_zero=True)
        self.setVisible(True)

    def _switch_stem(self, target_stem: str) -> None:
        """Seamlessly switch active stem while keeping playback position exact."""
        if target_stem == self._active_stem:
            return

        self._active_stem = target_stem
        self._apply_stem_source(seek_to_zero=False)

    def _apply_stem_source(self, seek_to_zero: bool = False) -> None:
        """Load selected stem audio, preserving playback state and time offset."""
        target_path: Optional[Path] = None
        if self._active_stem == "original":
            target_path = self._original_path
            title = "PRÉÉCOUTE : MIX ORIGINAL"
        elif self._active_stem == "vocals":
            target_path = self._vocals_path
            title = "PRÉÉCOUTE : VOIX ISOLÉE (ACAPELLA)"
        else:
            target_path = self._instru_path
            title = "PRÉÉCOUTE : INSTRUMENTALE"

        if not target_path or not target_path.exists():
            return

        self._label_track.setText(title)

        # Style active stem button
        active_style = "background-color: #ffffff; color: #000000; font-weight: 700; border: none;"
        inactive_style = "background-color: #161924; color: #94a3b8; font-weight: 600; border: 1px solid #282f40;"

        self._btn_vocals.setStyleSheet(active_style if self._active_stem == "vocals" else inactive_style)
        self._btn_instru.setStyleSheet(active_style if self._active_stem == "instru" else inactive_style)
        self._btn_orig.setStyleSheet(active_style if self._active_stem == "original" else inactive_style)

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
            self._btn_play.setText("Lecture")
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
