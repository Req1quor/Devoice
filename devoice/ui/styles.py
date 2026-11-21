"""Minimalist monochrome stylesheet for Devoice (Apple / Nothing OS aesthetic)."""

DARK_THEME = """
/* === Global Window & Fonts === */
QMainWindow, QWidget {
    background-color: #08080a;
    color: #e4e4e7;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #27272a;
    selection-color: #ffffff;
}

/* === Header Labels === */
#TitleLabel {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 11px;
    letter-spacing: 0.2px;
    color: #71717a;
}
#DeviceLabel {
    background-color: #121215;
    border: 1px solid #27272a;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #d4d4d8;
}

/* === Drop Zone (Minimalist Outline) === */
#DropZone {
    background-color: #0d0d10;
    border: 1.5px dashed #27272a;
    border-radius: 16px;
    min-height: 140px;
}
#DropZone:hover {
    border-color: #71717a;
    background-color: #141418;
}
#DropZoneLabel {
    color: #71717a;
    font-size: 13px;
    font-weight: 500;
}
#DropZoneIcon {
    font-size: 32px;
    color: #52525b;
}

/* === File List === */
QListWidget {
    background-color: #0d0d10;
    border: 1px solid #1f1f23;
    border-radius: 10px;
    padding: 6px;
    color: #e4e4e7;
}
QListWidget::item {
    background-color: #141418;
    border: 1px solid #1f1f23;
    border-radius: 6px;
    padding: 6px 12px;
    margin-bottom: 2px;
}
QListWidget::item:selected {
    border-color: #52525b;
    background-color: #1c1c22;
}

/* === Controls & Combobox === */
QLabel {
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 500;
}
QComboBox {
    background-color: #121215;
    border: 1px solid #242428;
    border-radius: 8px;
    padding: 6px 12px;
    color: #fafafa;
    font-weight: 500;
    min-height: 18px;
}
QComboBox:hover {
    border-color: #3f3f46;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #121215;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 4px;
    color: #fafafa;
    selection-background-color: #27272a;
}

/* === Diagnostic & Adaptive Options Card === */
#DiagnosticCard {
    background-color: #0e0e12;
    border: 1px solid #1f1f25;
    border-radius: 12px;
    padding: 12px 16px;
}
#DiagnosticTitle {
    color: #e4e4e7;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
}
#DiagnosticSummary {
    color: #71717a;
    font-size: 11px;
    font-weight: 400;
}
#ReasonLabel {
    color: #71717a;
    font-size: 11px;
    margin-left: 24px;
    margin-bottom: 4px;
}
#ReasonLabel[recommended="true"] {
    color: #4ade80;
}

/* === Checkboxes (Adaptive Options) === */
QCheckBox {
    color: #f4f4f5;
    font-size: 12px;
    font-weight: 600;
    spacing: 8px;
}
QCheckBox:hover {
    color: #ffffff;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    background-color: #121215;
}
QCheckBox::indicator:hover {
    border-color: #71717a;
}
QCheckBox::indicator:checked {
    background-color: #fafafa;
    border-color: #fafafa;
    image: none;
}

/* === Buttons === */
QPushButton {
    background-color: #141418;
    color: #f4f4f5;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #202026;
    border-color: #3f3f46;
}
QPushButton:pressed {
    background-color: #0c0c0e;
}

/* === Main Hero Action Button (Nothing / Apple High Contrast) === */
#StartButton {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
    padding: 10px 32px;
    min-height: 20px;
}
#StartButton:hover {
    background-color: #e4e4e7;
}
#StartButton:disabled {
    background-color: #27272a;
    color: #52525b;
}

/* === Progress Bar (Ultra Clean Line) === */
QProgressBar {
    background-color: #141418;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #fafafa;
    border-radius: 3px;
}

/* === Status Label === */
#StatusLabel {
    color: #71717a;
    font-size: 11px;
    font-weight: 500;
}

/* === Audio Player Section === */
#PlayerCard {
    background-color: #0d0d10;
    border: 1px solid #1f1f23;
    border-radius: 14px;
    padding: 14px;
}
#PillBtnActive {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 700;
}
#PillBtnInactive {
    background-color: #18181c;
    color: #a1a1aa;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}
#PillBtnInactive:hover {
    background-color: #24242c;
    color: #ffffff;
}

/* === Sliders (Timeline Scrubber) === */
QSlider::groove:horizontal {
    height: 4px;
    background: #1f1f23;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #fafafa;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #27272a;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    transform: scale(1.2);
}
"""
