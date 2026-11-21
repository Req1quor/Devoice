"""Dark Monospace ASCII / Dither / Terminal Hardware theme for Devoice."""

DARK_THEME = """
/* === Global Window & Monospace Typography === */
QMainWindow, QWidget {
    background-color: #08080a;
    color: #e4e4e7;
    font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: #27272a;
    selection-color: #ffffff;
}

/* === Top Terminal Banner === */
#TitleLabel {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 11px;
    letter-spacing: 0.5px;
    color: #71717a;
    font-weight: 500;
}
#DeviceLabel {
    background-color: #0d0d11;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #22c55e;
    letter-spacing: 0.5px;
}

/* === Drop Zone (ASCII / Dither Chassis) === */
#DropZone {
    background-color: #0a0a0d;
    border: 1px dashed #27272a;
    border-radius: 0px;
    min-height: 145px;
}
#DropZone:hover {
    border: 1px dashed #52525b;
    background-color: #0f0f14;
}
#DropZone[loaded="true"] {
    background-color: #0d0d12;
    border: 1px solid #3f3f46;
}
#DropZone[loaded="true"]:hover {
    border: 1px solid #71717a;
    background-color: #121218;
}
#DropZoneLabel {
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
#DropZoneIcon {
    font-size: 14px;
    color: #a1a1aa;
    font-weight: 700;
    letter-spacing: 1.5px;
}

/* === File List === */
QListWidget {
    background-color: #0a0a0d;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 4px;
    color: #e4e4e7;
    font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
}
QListWidget::item {
    background-color: #0f0f13;
    border: 1px solid #1f1f23;
    border-radius: 0px;
    padding: 6px 10px;
    margin-bottom: 2px;
}
QListWidget::item:selected {
    border-color: #52525b;
    background-color: #18181b;
    color: #ffffff;
}

/* === Labels & Text === */
QLabel {
    color: #a1a1aa;
    font-size: 11px;
}

/* === Combobox (Terminal Dropdown) === */
QComboBox {
    background-color: #0d0d11;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 6px 12px;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QComboBox:hover {
    border-color: #52525b;
    background-color: #121217;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #71717a;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #0a0a0d;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 4px;
    color: #e4e4e7;
    selection-background-color: #1f1f23;
    selection-color: #ffffff;
}

/* === Studio Rack Enclosure === */
#DiagnosticCard {
    background-color: #0a0a0d;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 12px 14px;
}
#DiagnosticTitle {
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
#DiagnosticSummary {
    color: #71717a;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* === Buttons (Industrial Terminal) === */
QPushButton {
    background-color: #0d0d11;
    color: #e4e4e7;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.6px;
}
QPushButton:hover {
    background-color: #18181b;
    border-color: #52525b;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #000000;
    border-color: #71717a;
}
QPushButton:disabled {
    background-color: #08080a;
    color: #3f3f46;
    border-color: #18181b;
}

/* === Hero Execute Button === */
QPushButton#StartButton {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    border-radius: 0px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.2px;
    padding: 12px 32px;
    min-height: 20px;
    min-width: 240px;
}
QPushButton#StartButton:hover {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
    color: #000000;
}
QPushButton#StartButton:pressed {
    background-color: #a1a1aa;
    color: #000000;
}
QPushButton#StartButton:disabled {
    background-color: #0f0f13;
    color: #3f3f46;
    border-color: #1f1f23;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: transparent;
    color: #ef4444;
    border: 1px solid #3f1d1d;
    border-radius: 0px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QPushButton#CancelButton:hover {
    background-color: #2b1111;
    border-color: #ef4444;
}

/* === Progress Bar (Block Terminal Gauge) === */
QProgressBar {
    background-color: #0d0d11;
    border: 1px solid #27272a;
    border-radius: 0px;
    height: 12px;
    text-align: center;
    color: #a1a1aa;
    font-size: 10px;
    font-weight: 700;
}
QProgressBar::chunk {
    background-color: #ffffff;
}

/* === Status Label === */
#StatusLabel {
    color: #71717a;
    font-size: 11px;
    letter-spacing: 0.5px;
    padding-top: 4px;
}

/* === Synchronized Audio Player === */
#PlayerCard {
    background-color: #0a0a0d;
    border: 1px solid #27272a;
    border-radius: 0px;
    padding: 10px 14px;
}

/* === Slider (Hardware Fader) === */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 0px;
}
QSlider::sub-page:horizontal {
    background-color: #52525b;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    border: 1px solid #ffffff;
    width: 8px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 0px;
}
QSlider::handle:horizontal:hover {
    background-color: #e4e4e7;
}

/* === Scrollbars === */
QScrollBar:vertical {
    border: none;
    background-color: #08080a;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #27272a;
    min-height: 20px;
    border-radius: 0px;
}
QScrollBar::handle:vertical:hover {
    background-color: #52525b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
