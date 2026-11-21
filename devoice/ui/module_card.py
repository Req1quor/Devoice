"""Terminal ASCII hardware rack module card widget for Devoice."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StudioModuleCard(QFrame):
    """Sharp ASCII / terminal rack module card with monospace parameters and ASCII status."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        default_param: str = "",
        default_reason: str = ":: EN ATTENTE D'UN FICHIER AUDIO...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StudioModuleCard")
        self._checked = False
        self._title_str = title
        self._param_str = default_param
        self._reason_str = default_reason
        self._recommended = False
        self._enabled = True

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._update_appearance()

    def _setup_ui(self) -> None:
        self.setFixedHeight(58)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # ASCII status indicator: [ON] vs [--]
        self._status_badge = QLabel("[--]")
        self._status_badge.setFixedWidth(36)
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_badge.setStyleSheet(
            "font-family: 'Consolas', 'Cascadia Code', monospace; "
            "font-size: 10px; font-weight: 700; color: #52525b; "
            "background-color: #0d0d11; border: 1px solid #1f1f23;"
        )
        top_row.addWidget(self._status_badge)

        self._lbl_title = QLabel(self._title_str.upper())
        self._lbl_title.setStyleSheet(
            "font-family: 'Consolas', 'Cascadia Code', monospace; "
            "font-weight: 700; font-size: 11px; color: #ffffff; letter-spacing: 0.5px;"
        )
        top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        self._lbl_param = QLabel(f"[ {self._param_str} ]" if self._param_str else "")
        self._lbl_param.setStyleSheet(
            "font-family: 'Consolas', 'Cascadia Code', monospace; "
            "font-size: 10px; font-weight: 700; color: #a1a1aa; "
            "background-color: #0d0d11; padding: 1px 6px; border: 1px solid #27272a;"
        )
        if not self._param_str:
            self._lbl_param.setVisible(False)
        top_row.addWidget(self._lbl_param)

        layout.addLayout(top_row)

        self._lbl_reason = QLabel(self._reason_str)
        self._lbl_reason.setStyleSheet(
            "font-family: 'Consolas', 'Cascadia Code', monospace; "
            "font-size: 10px; color: #71717a;"
        )
        layout.addWidget(self._lbl_reason)

    def mousePressEvent(self, event) -> None:
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        self._checked = checked
        self._update_appearance()

    def setEnabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self._update_appearance()

    def update_info(self, param_text: str, reason_text: str, recommended: bool = False) -> None:
        self._param_str = param_text
        self._reason_str = reason_text
        self._recommended = recommended

        if param_text:
            self._lbl_param.setText(f"[ {param_text} ]")
            self._lbl_param.setVisible(True)
        else:
            self._lbl_param.setVisible(False)

        # Prefix reason with terminal marker if not already present
        display_reason = reason_text if reason_text.startswith("::") else f":: {reason_text}"
        self._lbl_reason.setText(display_reason)
        if recommended:
            self._lbl_reason.setStyleSheet(
                "font-family: 'Consolas', 'Cascadia Code', monospace; "
                "font-size: 10px; font-weight: 600; color: #22c55e;"
            )
        else:
            self._lbl_reason.setStyleSheet(
                "font-family: 'Consolas', 'Cascadia Code', monospace; "
                "font-size: 10px; color: #71717a;"
            )

    def _update_appearance(self) -> None:
        if not self._enabled:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #08080a;
                    border: 1px solid #141416;
                    border-radius: 0px;
                }
            """)
            self._status_badge.setText("[--]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 600; "
                "color: #27272a; background-color: #08080a; border: 1px solid #141416;"
            )
            self._lbl_title.setStyleSheet(
                "font-family: 'Consolas', monospace; font-weight: 500; font-size: 11px; color: #3f3f46;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; color: #3f3f46; "
                "background-color: #08080a; padding: 1px 6px; border: 1px solid #141416;"
            )
            return

        self._lbl_title.setStyleSheet(
            "font-family: 'Consolas', monospace; font-weight: 700; font-size: 11px; "
            "color: #ffffff; letter-spacing: 0.5px;"
        )

        if self._checked:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #0f0f14;
                    border: 1px solid #3f3f46;
                    border-radius: 0px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #71717a;
                    background-color: #14141a;
                }
            """)
            self._status_badge.setText("[ON]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                "color: #22c55e; background-color: #121217; border: 1px solid #22c55e;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                "color: #ffffff; background-color: #18181b; padding: 1px 6px; border: 1px solid #52525b;"
            )
        else:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #0a0a0d;
                    border: 1px solid #1f1f23;
                    border-radius: 0px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #3f3f46;
                    background-color: #0e0e12;
                }
            """)
            self._status_badge.setText("[--]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 600; "
                "color: #52525b; background-color: #0d0d11; border: 1px solid #1f1f23;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 500; "
                "color: #71717a; background-color: #0f0f13; padding: 1px 6px; border: 1px solid #27272a;"
            )
