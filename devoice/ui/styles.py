"""Pristine Noir & Blanc (Monochrome) theme for Devoice."""

DARK_THEME = """
/* === Global Settings === */
QMainWindow {
    background-color: #09090b;
}
QWidget {
    color: #e4e4e7;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 12px;
}
QLabel, QCheckBox {
    background: transparent;
}

/* === Header === */
#TitleLabel {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.3px;
    color: #ffffff;
}
#DeviceBadge {
    background-color: #141416;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #a1a1aa;
}

/* === Drop Zone (Noir & Blanc) === */
#DropZone {
    background-color: #111113;
    border: 1px dashed #27272a;
    border-radius: 8px;
    min-height: 115px;
}
#DropZone:hover {
    border: 1px dashed #71717a;
    background-color: #161619;
}
#DropZone[loaded="true"] {
    background-color: #121215;
    border: 1px solid #ffffff;
}
#DropZone[loaded="true"]:hover {
    border: 1px solid #ffffff;
    background-color: #16161a;
}

/* === Cards & Panels === */
#SettingsCard, #PlayerCard {
    background-color: #111113;
    border: 1px solid #222225;
    border-radius: 8px;
}

/* === Form Controls (Combos & Inputs) === */
QLabel {
    color: #a1a1aa;
    font-size: 12px;
}
QComboBox {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
    font-size: 12px;
    font-weight: 500;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #52525b;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a1a1aa;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 4px;
    color: #ffffff;
    selection-background-color: #27272a;
    selection-color: #ffffff;
}

/* === Standard Buttons === */
QPushButton {
    background-color: #18181b;
    color: #e4e4e7;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #27272a;
    border-color: #52525b;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #09090b;
}

/* === Primary Action Button (White Hero) === */
QPushButton#PrimaryButton {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
    padding: 10px 24px;
    min-height: 22px;
}
QPushButton#PrimaryButton:hover {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
    color: #000000;
}
QPushButton#PrimaryButton:pressed {
    background-color: #a1a1aa;
    color: #000000;
}
QPushButton#PrimaryButton:disabled {
    background-color: #141416;
    color: #52525b;
    border-color: #222225;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: transparent;
    color: #ef4444;
    border: 1px solid #3f1d1d;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton#CancelButton:hover {
    background-color: #221010;
    border-color: #ef4444;
}

/* === YouTube Ingest Bar === */
QLineEdit#YouTubeInput {
    background-color: #111113;
    color: #ffffff;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    selection-background-color: #27272a;
    selection-color: #ffffff;
}
QLineEdit#YouTubeInput:focus {
    border-color: #71717a;
    background-color: #141417;
}
QPushButton#YouTubeButton {
    background-color: #18181b;
    color: #e4e4e7;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#YouTubeButton:hover {
    background-color: #27272a;
    border-color: #52525b;
    color: #ffffff;
}
QPushButton#YouTubeButton:pressed {
    background-color: #09090b;
}
QPushButton#YouTubeButton:disabled {
    color: #52525b;
    border-color: #222225;
    background-color: #141416;
}

/* === Pristine Monochrome Checkboxes === */
QCheckBox {
    color: #e4e4e7;
    font-size: 12px;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #3f3f46;
    background-color: #18181b;
}
QCheckBox::indicator:hover {
    border-color: #a1a1aa;
}
QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
}
QCheckBox::indicator:disabled {
    border-color: #27272a;
    background-color: #121214;
}

/* === Progress Bar (Minimalist Monochrome Line) === */
QProgressBar {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 3px;
}

/* === Scrubber Slider === */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #222226;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: #ffffff;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    width: 12px;
    height: 12px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background-color: #e4e4e7;
}

/* === Modern Segmented Player Buttons === */
QPushButton#PlayButton {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    font-weight: 700;
    border-radius: 6px;
    padding: 6px 16px;
}
QPushButton#PlayButton:hover {
    background-color: #e4e4e7;
}
QPushButton#StemActive {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    font-weight: 700;
    border-radius: 6px;
}
QPushButton#StemInactive {
    background-color: #18181b;
    color: #a1a1aa;
    border: 1px solid #27272a;
    border-radius: 6px;
}
QPushButton#StemInactive:hover {
    background-color: #27272a;
    color: #ffffff;
}
"""
