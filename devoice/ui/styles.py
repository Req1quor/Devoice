"""Minimalist high-end studio stylesheet for Devoice (Teenage Engineering / Nothing OS / Apple aesthetic)."""

DARK_THEME = """
/* === Global Window & Fonts === */
QMainWindow, QWidget {
    background-color: #070709;
    color: #e4e4e7;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #272732;
    selection-color: #ffffff;
}

/* === Header Labels === */
#TitleLabel {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.6px;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 11px;
    letter-spacing: 0.3px;
    color: #71717a;
    font-weight: 500;
}
#DeviceLabel {
    background-color: #0f1016;
    border: 1px solid #1f2230;
    border-radius: 12px;
    padding: 5px 14px;
    font-size: 11px;
    font-weight: 600;
    color: #d4d4d8;
}

/* === Drop Zone (Modern Deck) === */
#DropZone {
    background-color: #0b0b0f;
    border: 1.5px dashed #22232e;
    border-radius: 16px;
    min-height: 155px;
}
#DropZone:hover {
    border-color: #4f5370;
    background-color: #101118;
}
#DropZone[loaded="true"] {
    background-color: #0f111a;
    border: 1.5px solid #2e3248;
}
#DropZone[loaded="true"]:hover {
    border-color: #555b82;
    background-color: #141724;
}
#DropZoneLabel {
    color: #d4d4d8;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
#DropZoneIcon {
    font-size: 28px;
    color: #71717a;
}

/* === File List === */
QListWidget {
    background-color: #0b0b0f;
    border: 1px solid #1c1c24;
    border-radius: 10px;
    padding: 6px;
    color: #e4e4e7;
}
QListWidget::item {
    background-color: #121218;
    border: 1px solid #1c1c24;
    border-radius: 6px;
    padding: 6px 12px;
    margin-bottom: 2px;
}
QListWidget::item:selected {
    border-color: #4b4e69;
    background-color: #181922;
}

/* === Controls & Combobox === */
QLabel {
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 500;
}
QComboBox {
    background-color: #0f1016;
    border: 1px solid #222432;
    border-radius: 8px;
    padding: 7px 14px;
    color: #fafafa;
    font-weight: 600;
    font-size: 12px;
    min-height: 18px;
}
QComboBox:hover {
    border-color: #3f435c;
    background-color: #14151e;
}
QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #0f1016;
    border: 1px solid #272a3a;
    border-radius: 8px;
    padding: 6px;
    color: #fafafa;
    selection-background-color: #242738;
}

/* === Studio Rack & Diagnostic Card === */
#DiagnosticCard {
    background-color: #0c0d12;
    border: 1px solid #1c1d28;
    border-radius: 14px;
    padding: 14px 16px;
}
#DiagnosticTitle {
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
#DiagnosticSummary {
    color: #8b8ea4;
    font-size: 11px;
    font-weight: 500;
}

/* === Buttons === */
QPushButton {
    background-color: #13141c;
    color: #f4f4f5;
    border: 1px solid #242636;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #1d1e2b;
    border-color: #3b3e56;
}
QPushButton:pressed {
    background-color: #0c0d12;
}

/* === Hero Start Action Button === */
QPushButton#StartButton {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 22px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.4px;
    padding: 12px 36px;
    min-height: 20px;
    min-width: 220px;
}
QPushButton#StartButton:hover {
    background-color: #eaeaea;
    color: #000000;
}
QPushButton#StartButton:pressed {
    background-color: #d4d4d8;
    color: #000000;
}
QPushButton#StartButton:disabled {
    background-color: #1a1a22;
    color: #52525b;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: transparent;
    color: #ef4444;
    border: 1px solid #3f1d1d;
    border-radius: 18px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#CancelButton:hover {
    background-color: #2b1111;
    border-color: #7f1d1d;
}

/* === Progress Bar (Ultra Clean Line) === */
QProgressBar {
    background-color: #13141c;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 3px;
}

/* === Status Label === */
#StatusLabel {
    color: #8b8ea4;
    font-size: 11px;
    font-weight: 500;
}

/* === Audio Player Section === */
#PlayerCard {
    background-color: #0c0d12;
    border: 1px solid #1c1d28;
    border-radius: 14px;
    padding: 14px 16px;
}
#PillBtnActive {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 7px;
    padding: 7px 16px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.3px;
}
#PillBtnInactive {
    background-color: #14151e;
    color: #9497ab;
    border: 1px solid #232536;
    border-radius: 7px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.3px;
}
#PillBtnInactive:hover {
    background-color: #1e202e;
    border-color: #3b3e58;
    color: #ffffff;
}

/* === Sliders (Timeline Scrubber) === */
QSlider::groove:horizontal {
    height: 4px;
    background: #1c1d28;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #ffffff;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #272732;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
    transform: scale(1.2);
}
"""
