"""High-Contrast Dark Monospace ASCII / Dither / Terminal Hardware theme for Devoice."""

DARK_THEME = """
/* === Global Window & Typography === */
QMainWindow, QWidget {
    background-color: #0b0c10;
    color: #e2e8f0;
    font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: #334155;
    selection-color: #ffffff;
}

/* === Top Terminal Banner === */
#TitleLabel {
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 1.2px;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 11px;
    letter-spacing: 0.6px;
    color: #94a3b8;
    font-weight: 600;
}
#DeviceLabel {
    background-color: #0a1f16;
    border: 1px solid #166534;
    border-radius: 0px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 700;
    color: #4ade80;
    letter-spacing: 0.8px;
}

/* === Drop Zone (High-Contrast Dither Frame) === */
#DropZone {
    background-color: #12141c;
    border: 1.5px dashed #334155;
    border-radius: 0px;
    min-height: 145px;
}
#DropZone:hover {
    border: 1.5px dashed #64748b;
    background-color: #161924;
}
#DropZone[loaded="true"] {
    background-color: #131722;
    border: 1.5px solid #22c55e;
}
#DropZone[loaded="true"]:hover {
    border: 1.5px solid #4ade80;
    background-color: #181d2a;
}
#DropZoneLabel {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
#DropZoneIcon {
    font-size: 14px;
    color: #e2e8f0;
    font-weight: 800;
    letter-spacing: 1.5px;
}

/* === File List === */
QListWidget {
    background-color: #12141c;
    border: 1px solid #2d3345;
    border-radius: 0px;
    padding: 4px;
    color: #f1f5f9;
    font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
}
QListWidget::item {
    background-color: #181b26;
    border: 1px solid #2d3345;
    border-radius: 0px;
    padding: 6px 12px;
    margin-bottom: 3px;
}
QListWidget::item:selected {
    border-color: #64748b;
    background-color: #262c3e;
    color: #ffffff;
}

/* === Labels & Technical Typography === */
QLabel {
    color: #cbd5e1;
    font-size: 11px;
}

/* === Combobox (Terminal Dropdown) === */
QComboBox {
    background-color: #141722;
    border: 1px solid #334155;
    border-radius: 0px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QComboBox:hover {
    border-color: #64748b;
    background-color: #1a1e2c;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #12141d;
    border: 1px solid #334155;
    border-radius: 0px;
    padding: 4px;
    color: #f8fafc;
    selection-background-color: #283044;
    selection-color: #ffffff;
}

/* === Studio Rack Enclosure === */
#DiagnosticCard {
    background-color: #10121a;
    border: 1px solid #262b3a;
    border-radius: 0px;
    padding: 14px 16px;
}
#DiagnosticTitle {
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
}
#DiagnosticSummary {
    color: #38bdf8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
}

/* === Buttons (Industrial Terminal) === */
QPushButton {
    background-color: #151824;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 0px;
    padding: 8px 18px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.6px;
}
QPushButton:hover {
    background-color: #22273a;
    border-color: #64748b;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #0b0c12;
    border-color: #94a3b8;
}
QPushButton:disabled {
    background-color: #0e1017;
    color: #475569;
    border-color: #1e2330;
}

/* === Hero Execute Button (High-Impact Inversion) === */
QPushButton#StartButton {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    border-radius: 0px;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 1.5px;
    padding: 13px 36px;
    min-height: 22px;
    min-width: 260px;
}
QPushButton#StartButton:hover {
    background-color: #38bdf8;
    border-color: #38bdf8;
    color: #000000;
}
QPushButton#StartButton:pressed {
    background-color: #0284c7;
    color: #ffffff;
}
QPushButton#StartButton:disabled {
    background-color: #141722;
    color: #475569;
    border: 1px solid #23293a;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: #1f1115;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 0px;
    padding: 8px 20px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.6px;
}
QPushButton#CancelButton:hover {
    background-color: #3b171c;
    border-color: #ef4444;
    color: #ffffff;
}

/* === Progress Bar (Block Terminal Gauge) === */
QProgressBar {
    background-color: #12141c;
    border: 1px solid #334155;
    border-radius: 0px;
    height: 14px;
    text-align: center;
    color: #ffffff;
    font-size: 10px;
    font-weight: 800;
}
QProgressBar::chunk {
    background-color: #22c55e;
}

/* === Status Label === */
#StatusLabel {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
    padding-top: 4px;
}

/* === Synchronized Audio Player === */
#PlayerCard {
    background-color: #12141c;
    border: 1px solid #2d3345;
    border-radius: 0px;
    padding: 12px 16px;
}

/* === Slider (Hardware Fader) === */
QSlider::groove:horizontal {
    height: 5px;
    background-color: #1e2332;
    border: 1px solid #334155;
    border-radius: 0px;
}
QSlider::sub-page:horizontal {
    background-color: #38bdf8;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    border: 1px solid #ffffff;
    width: 10px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 0px;
}
QSlider::handle:horizontal:hover {
    background-color: #38bdf8;
}

/* === Scrollbars === */
QScrollBar:vertical {
    border: none;
    background-color: #0b0c10;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #334155;
    min-height: 24px;
    border-radius: 0px;
}
QScrollBar::handle:vertical:hover {
    background-color: #64748b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
