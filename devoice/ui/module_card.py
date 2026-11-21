"""Interactive studio rack module card widget for Devoice."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StudioModuleCard(QFrame):
    """Sleek tactile studio rack module card with status LED and parameter chip."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        default_param: str = "",
        default_reason: str = "En attente d'un fichier audio…",
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
        self.setFixedHeight(64)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._led = QLabel("○")
        self._led.setFixedWidth(14)
        top_row.addWidget(self._led)

        self._lbl_title = QLabel(self._title_str)
        self._lbl_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #f4f4f5; letter-spacing: 0.2px;")
        top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        self._lbl_param = QLabel(self._param_str)
        self._lbl_param.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #a1a1aa; "
            "background-color: #181822; padding: 2px 7px; border-radius: 4px; "
            "border: 1px solid #232330;"
        )
        if not self._param_str:
            self._lbl_param.setVisible(False)
        top_row.addWidget(self._lbl_param)

        layout.addLayout(top_row)

        self._lbl_reason = QLabel(self._reason_str)
        self._lbl_reason.setStyleSheet("font-size: 10px; color: #71717a;")
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
            self._lbl_param.setText(param_text)
            self._lbl_param.setVisible(True)
        else:
            self._lbl_param.setVisible(False)

        self._lbl_reason.setText(reason_text)
        if recommended:
            self._lbl_reason.setStyleSheet("font-size: 10px; font-weight: 500; color: #4ade80;")
        else:
            self._lbl_reason.setStyleSheet("font-size: 10px; color: #71717a;")

    def _update_appearance(self) -> None:
        if not self._enabled:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #09090c;
                    border: 1px solid #14141a;
                    border-radius: 9px;
                }
            """)
            self._led.setText("○")
            self._led.setStyleSheet("color: #3f3f46; font-size: 12px;")
            self._lbl_title.setStyleSheet("font-weight: 500; font-size: 12px; color: #52525b;")
            return

        self._lbl_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #f4f4f5; letter-spacing: 0.2px;")

        if self._checked:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #101118;
                    border: 1px solid #2d3042;
                    border-radius: 9px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #4f5370;
                    background-color: #14151f;
                }
            """)
            self._led.setText("●")
            self._led.setStyleSheet("color: #22c55e; font-size: 13px;")
            self._lbl_param.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #ffffff; "
                "background-color: #202230; padding: 2px 7px; border-radius: 4px; "
                "border: 1px solid #363950;"
            )
        else:
            self.setStyleSheet("""
                QFrame#StudioModuleCard {
                    background-color: #0b0b0e;
                    border: 1px solid #181820;
                    border-radius: 9px;
                }
                QFrame#StudioModuleCard:hover {
                    border-color: #262632;
                    background-color: #0f0f13;
                }
            """)
            self._led.setText("○")
            self._led.setStyleSheet("color: #52525b; font-size: 13px;")
            self._lbl_param.setStyleSheet(
                "font-size: 10px; font-weight: 600; color: #71717a; "
                "background-color: #14141c; padding: 2px 7px; border-radius: 4px; "
                "border: 1px solid #1e1e28;"
            )
