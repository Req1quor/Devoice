"""Synchronized A/B/C audio preview player for Original, Acapella, and Instrumental."""

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
        self._active_stem: str = "vocals"  # "original", "vocals", or "instru"

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
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        # Header with active track name and time
        top_row = QHBoxLayout()
        self._label_track = QLabel(">> PREVISUALISATION AUDIO")
        self._label_track.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; color: #a1a1aa; letter-spacing: 0.8px;"
        )
        
        self._label_time = QLabel("[ 00:00 / 00:00 ]")
        self._label_time.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; color: #71717a;"
        )

        top_row.addWidget(self._label_track)
        top_row.addStretch()
        top_row.addWidget(self._label_time)
        card_layout.addLayout(top_row)

        # Controls row: Play button + Stem selectors (Original / Acapella / Instru)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self._btn_play = QPushButton("[ > ]")
        self._btn_play.setFixedWidth(48)
        self._btn_play.clicked.connect(self._toggle_play)
        controls_row.addWidget(self._btn_play)

        controls_row.addSpacing(6)

        self._btn_orig = QPushButton("[ ORIGINAL ]")
        self._btn_orig.clicked.connect(lambda: self._switch_stem("original"))
        controls_row.addWidget(self._btn_orig)

        self._btn_vocals = QPushButton("[ ACAPELLA ]")
        self._btn_vocals.clicked.connect(lambda: self._switch_stem("vocals"))
        controls_row.addWidget(self._btn_vocals)

        self._btn_instru = QPushButton("[ INSTRU ]")
        self._btn_instru.clicked.connect(lambda: self._switch_stem("instru"))
        controls_row.addWidget(self._btn_instru)

        controls_row.addStretch()
        card_layout.addLayout(controls_row)

        # Scrubber Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderMoved.connect(self._seek)
        card_layout.addWidget(self._slider)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.addWidget(card)

    # ── Public API ──────────────────────────────────────────────────────

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

        # Auto-select Vocals by default
        self._active_stem = "vocals"
        self._apply_stem_source(seek_to_zero=True)
        self.setVisible(True)

    # ── Synchronized Stem Switching ─────────────────────────────────────

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
            title = "MIX ORIGINAL"
        elif self._active_stem == "vocals":
            target_path = self._vocals_path
            title = "ACAPELLA (VOIX ISOLÉE)"
        else:
            target_path = self._instru_path
            title = "INSTRUMENTALE"

        if not target_path or not target_path.exists():
            return

        self._label_track.setText(title)

        # Update visual button styles (monochrome active vs inactive)
        self._btn_orig.setObjectName("PillBtnActive" if self._active_stem == "original" else "PillBtnInactive")
        self._btn_vocals.setObjectName("PillBtnActive" if self._active_stem == "vocals" else "PillBtnInactive")
        self._btn_instru.setObjectName("PillBtnActive" if self._active_stem == "instru" else "PillBtnInactive")

        for btn in (self._btn_orig, self._btn_vocals, self._btn_instru):
            btn.setStyle(btn.style())  # Force QSS refresh

        was_playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        current_pos = 0 if seek_to_zero else self._player.position()

        self._player.setSource(QUrl.fromLocalFile(str(target_path)))
        if current_pos > 0:
            self._player.setPosition(current_pos)

        if was_playing:
            self._player.play()
            self._btn_play.setText("[ || ]")

    # ── Playback Helpers ────────────────────────────────────────────────

    def _toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._btn_play.setText("[ > ]")
        else:
            self._player.play()
            self._btn_play.setText("[ || ]")

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
        pos_str = f"{pos_s // 60:02d}:{pos_s % 60:02d}"
        dur_str = f"{dur_s // 60:02d}:{dur_s % 60:02d}"
        self._label_time.setText(f"{pos_str} / {dur_str}")
