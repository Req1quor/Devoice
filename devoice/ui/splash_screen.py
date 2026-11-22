"""Studio-grade splash screen with smooth waveform animation and fade-out transition."""

from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class StudioSplashScreen(QWidget):
    """Minimalist studio splash screen with animated stem frequency bars."""

    splash_finished = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(420, 260)

        # Center on screen
        screen = self.screen() or (self.window().screen() if self.window() else None)
        if screen:
            geo = screen.geometry()
            self.move((geo.width() - 420) // 2, (geo.height() - 260) // 2)

        self._tick: float = 0.0
        self._status_text: str = "Initialisation du moteur audio…"

        # Opacity effect for smooth fade-in and fade-out
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(25)  # ~40 fps
        self._anim_timer.timeout.connect(self._on_anim_tick)

        # Pulse animation timer
        self._fade_animation: QPropertyAnimation | None = None

    def start_animation(self) -> None:
        """Fade in and start the fluid waveform pulses."""
        self.show()
        self._anim_timer.start()

        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(400)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.start()

        # Step-by-step progress status texts
        QTimer.singleShot(700, lambda: self.set_status("Chargement des réseaux neuronaux…"))
        QTimer.singleShot(1400, lambda: self.set_status("Vérification accélération CUDA…"))
        QTimer.singleShot(2000, lambda: self.set_status("Prêt."))
        QTimer.singleShot(2300, self.finish_splash)

    def set_status(self, text: str) -> None:
        self._status_text = text
        self.update()

    def finish_splash(self) -> None:
        """Fade out smoothly and emit splash_finished."""
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(350)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_animation.finished.connect(self._on_fade_out_finished)
        self._fade_animation.start()

    def _on_fade_out_finished(self) -> None:
        self._anim_timer.stop()
        self.close()
        self.splash_finished.emit()

    def _on_anim_tick(self) -> None:
        self._tick += 0.08
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Dark Rounded Chassis
        chassis_rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        chassis_path = QPainterPath()
        chassis_path.addRoundedRect(chassis_rect, 16, 16)

        # Solid deep black background
        painter.fillPath(chassis_path, QColor(9, 9, 11))

        # Crisp subtle border (#27272a)
        painter.setPen(QColor(39, 39, 42))
        painter.drawPath(chassis_path)

        # 2. Brand Name: DEVOICE
        painter.setPen(QColor(255, 255, 255))
        font_brand = QFont("Segoe UI", 18, QFont.Weight.ExtraBold)
        font_brand.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3.5)
        painter.setFont(font_brand)
        painter.drawText(QRectF(0, 48, self.width(), 32), Qt.AlignmentFlag.AlignCenter, "DEVOICE")

        # Subtitle
        painter.setPen(QColor(161, 161, 170))
        font_sub = QFont("Segoe UI", 9, QFont.Weight.Medium)
        font_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        painter.setFont(font_sub)
        painter.drawText(
            QRectF(0, 82, self.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "STUDIO AUDIO SEPARATION",
        )

        # 3. Dynamic Stem Frequency Waveform (Audio Pulsing Animation)
        cx = self.width() / 2
        cy = 145
        num_bars = 11
        bar_width = 4.0
        bar_spacing = 9.0
        start_x = cx - ((num_bars * (bar_width + bar_spacing) - bar_spacing) / 2)

        for i in range(num_bars):
            bx = start_x + i * (bar_width + bar_spacing)
            # Distance from center factor for diamond envelope
            dist_factor = 1.0 - (abs(i - (num_bars // 2)) / (num_bars / 2))
            # Smooth undulating wave
            wave = (math.sin(self._tick * 1.5 + i * 0.6) + 1.0) / 2.0
            height = 8.0 + dist_factor * 34.0 * (0.35 + 0.65 * wave)

            # Central gap separating vocal & instrumental stems
            gap = 3.5

            # Top bar (vocals)
            top_rect = QRectF(bx, cy - gap - height / 2, bar_width, height / 2)
            # Bottom bar (instrumentals)
            bot_rect = QRectF(bx, cy + gap, bar_width, height / 2)

            # Fade edges slightly
            alpha = int(140 + 115 * dist_factor)
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(top_rect, 2, 2)
            painter.drawRoundedRect(bot_rect, 2, 2)

        # 4. Status Indicator Readout at Bottom
        painter.setPen(QColor(113, 113, 122))
        font_status = QFont("Segoe UI", 9, QFont.Weight.Normal)
        painter.setFont(font_status)
        painter.drawText(
            QRectF(0, self.height() - 44, self.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self._status_text,
        )
