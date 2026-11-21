"""High-Contrast Terminal ASCII hardware rack module card widget for Devoice."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StudioModuleCard(QFrame):
    """High-contrast ASCII / terminal rack module card with word-wrap and clear visibility."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        default_param: str = "",
        default_reason: str = ":: En attente d'un fichier audio pour calibrage...",
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
        self.setFixedHeight(74)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # High-contrast ASCII status indicator
        self._status_badge = QLabel("[ BYPASS ]")
        self._status_badge.setFixedWidth(64)
        self._status_badge.setFixedHeight(22)
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_badge.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 800; "
            "color: #94a3b8; background-color: #1a1e2c; border: 1px solid #384259;"
        )
        top_row.addWidget(self._status_badge)

        self._lbl_title = QLabel(self._title_str.upper())
        self._lbl_title.setStyleSheet(
            "font-family: 'Consolas', monospace; font-weight: 800; font-size: 12px; "
            "color: #ffffff; letter-spacing: 0.6px;"
        )
        top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        self._lbl_param = QLabel(f"[ {self._param_str} ]" if self._param_str else "")
        self._lbl_param.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 800; "
            "color: #f8fafc; background-color: #243048; padding: 2px 8px; border: 1px solid #3e5178;"
        )
        if not self._param_str:
            self._lbl_param.setVisible(False)
        top_row.addWidget(self._lbl_param)

        layout.addLayout(top_row)

        self._lbl_reason = QLabel(self._reason_str)
        self._lbl_reason.setWordWrap(True)
        self._lbl_reason.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; color: #94a3b8; line-height: 14px;"
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

        display_reason = reason_text if reason_text.startswith("::") else f":: {reason_text}"
        self._lbl_reason.setText(display_reason)
        if recommended:
            self._lbl_reason.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600; color: #4ade80;"
            )
        else:
            self._lbl_reason.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; color: #cbd5e1;"
            )

    def _update_appearance(self) -> None:
        if not self._enabled:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #10121a;
                    border: 1px solid #232938;
                    border-radius: 0px;
                }
            """)
            self._status_badge.setText("[ BYPASS ]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                "color: #475569; background-color: #141722; border: 1px solid #232938;"
            )
            self._lbl_title.setStyleSheet(
                "font-family: 'Consolas', monospace; font-weight: 700; font-size: 12px; color: #64748b;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; color: #64748b; "
                "background-color: #141722; padding: 2px 8px; border: 1px solid #232938;"
            )
            return

        self._lbl_title.setStyleSheet(
            "font-family: 'Consolas', monospace; font-weight: 800; font-size: 12px; "
            "color: #ffffff; letter-spacing: 0.6px;"
        )

        if self._checked:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #172030;
                    border: 1.5px solid #22c55e;
                    border-radius: 0px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #4ade80;
                    background-color: #1d283c;
                }
            """)
            self._status_badge.setText("[ ON ]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 900; "
                "color: #22c55e; background-color: #0d281e; border: 1px solid #22c55e;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 800; "
                "color: #ffffff; background-color: #273650; padding: 2px 8px; border: 1px solid #4ade80;"
            )
        else:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #141722;
                    border: 1px solid #2c3447;
                    border-radius: 0px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #64748b;
                    background-color: #191d2c;
                }
            """)
            self._status_badge.setText("[ BYPASS ]")
            self._status_badge.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                "color: #94a3b8; background-color: #1c2130; border: 1px solid #384259;"
            )
            self._lbl_param.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; "
                "color: #cbd5e1; background-color: #1c2130; padding: 2px 8px; border: 1px solid #333e54;"
            )
