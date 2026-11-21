"""Modern sleek minimalist dark theme for Devoice (Linear / Raycast / Apple Pro aesthetic)."""

DARK_THEME = """
/* === Global Window & Typography === */
QMainWindow, QWidget {
    background-color: #0b0c10;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

/* === Top App Header === */
#TitleLabel {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 500;
}
#DeviceBadge {
    background-color: #121622;
    border: 1px solid #1e2638;
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #34d399;
}

/* === Drop Zone (Modern Clean Card) === */
#DropZone {
    background-color: #11131a;
    border: 1.5px dashed #282f42;
    border-radius: 14px;
    min-height: 140px;
}
#DropZone:hover {
    border-color: #3b82f6;
    background-color: #141724;
}
#DropZone[loaded="true"] {
    background-color: #131724;
    border: 1.5px solid #22c55e;
}
#DropZone[loaded="true"]:hover {
    border-color: #4ade80;
    background-color: #161b2b;
}

/* === Surface Panels / Cards === */
#SettingsCard, #AdvancedDrawer, #PlayerCard {
    background-color: #11131a;
    border: 1px solid #1e222f;
    border-radius: 12px;
}

/* === Combobox & Inputs === */
QComboBox {
    background-color: #151822;
    border: 1px solid #282f40;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
}
QComboBox:hover {
    border-color: #3b82f6;
    background-color: #1a1e2b;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #141722;
    border: 1px solid #282f40;
    border-radius: 8px;
    padding: 6px;
    color: #f1f5f9;
    selection-background-color: #273046;
    selection-color: #ffffff;
}

/* === Buttons === */
QPushButton {
    background-color: #161924;
    color: #f1f5f9;
    border: 1px solid #282f40;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #212638;
    border-color: #3e4862;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #0f1118;
}

/* === Hero Primary Action Button === */
QPushButton#HeroButton {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.2px;
    padding: 13px 28px;
    min-height: 22px;
}
QPushButton#HeroButton:hover {
    background-color: #e2e8f0;
    color: #000000;
}
QPushButton#HeroButton:pressed {
    background-color: #cbd5e1;
    color: #000000;
}
QPushButton#HeroButton:disabled {
    background-color: #161822;
    color: #475569;
    border: 1px solid #202434;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: transparent;
    color: #f87171;
    border: 1px solid #451a1a;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#CancelButton:hover {
    background-color: #2a1215;
    border-color: #ef4444;
}

/* === Modern Clean Checkbox === */
QCheckBox {
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 500;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #333d54;
    background-color: #141722;
}
QCheckBox::indicator:hover {
    border-color: #3b82f6;
    background-color: #1a1e2b;
}
QCheckBox::indicator:checked {
    background-color: #22c55e;
    border-color: #22c55e;
    image: none;
}
QCheckBox::indicator:disabled {
    border-color: #202434;
    background-color: #0f1118;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #11131a;
    border: 1px solid #202534;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}

/* === Sliders === */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #1e2434;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: #3b82f6;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    width: 14px;
    height: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background-color: #60a5fa;
}

/* === Scrollbars === */
QScrollBar:vertical {
    border: none;
    background-color: #0b0c10;
    width: 6px;
}
QScrollBar::handle:vertical {
    background-color: #242a3a;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background-color: #384259;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
