"""Unified, consistent, minimalist dark theme for Devoice."""

DARK_THEME = """
/* === Global Settings === */
QMainWindow {
    background-color: #0c0d12;
}
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 12px;
}
QLabel, QCheckBox {
    background: transparent;
}

/* === Header === */
#TitleLabel {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}
#SubtitleLabel {
    font-size: 12px;
    color: #8a90a4;
}
#DeviceBadge {
    background-color: #161822;
    border: 1px solid #262a38;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
    color: #8a90a4;
}

/* === Drop Zone === */
#DropZone {
    background-color: #12141c;
    border: 1px dashed #282d3e;
    border-radius: 8px;
    min-height: 120px;
}
#DropZone:hover {
    border-color: #3b82f6;
    background-color: #141722;
}
#DropZone[loaded="true"] {
    background-color: #12141c;
    border: 1px solid #3b82f6;
}

/* === Panels / Cards === */
#SettingsCard, #PlayerCard {
    background-color: #12141c;
    border: 1px solid #232736;
    border-radius: 8px;
    padding: 14px;
}

/* === Form Controls (Combos & Inputs) === */
QLabel {
    color: #8a90a4;
    font-size: 12px;
}
QComboBox {
    background-color: #161822;
    border: 1px solid #262a38;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f3f9;
    font-size: 12px;
    min-height: 18px;
}
QComboBox:hover {
    border-color: #3d445c;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8a90a4;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #161822;
    border: 1px solid #262a38;
    border-radius: 6px;
    padding: 4px;
    color: #f1f3f9;
    selection-background-color: #242938;
}

/* === Buttons === */
QPushButton {
    background-color: #161822;
    color: #e2e8f0;
    border: 1px solid #262a38;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #1e2230;
    border-color: #3d445c;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #10121a;
}

/* === Primary Action Button === */
QPushButton#PrimaryButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 24px;
    min-height: 20px;
}
QPushButton#PrimaryButton:hover {
    background-color: #2563eb;
    border-color: #2563eb;
}
QPushButton#PrimaryButton:pressed {
    background-color: #1d4ed8;
}
QPushButton#PrimaryButton:disabled {
    background-color: #161822;
    color: #555c70;
    border-color: #232736;
}

/* === Cancel Button === */
QPushButton#CancelButton {
    background-color: transparent;
    color: #ef4444;
    border: 1px solid #4a1d1d;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton#CancelButton:hover {
    background-color: #221010;
    border-color: #ef4444;
}

/* === Checkboxes === */
QCheckBox {
    color: #f1f3f9;
    font-size: 12px;
    spacing: 8px;
    min-height: 20px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #2d3244;
    background-color: #161822;
}
QCheckBox::indicator:hover {
    border-color: #3b82f6;
}
QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}
QCheckBox::indicator:disabled {
    border-color: #1d212d;
    background-color: #12141c;
}
#AutoSubLabel {
    font-size: 11px;
    color: #8a90a4;
    padding-left: 24px;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #12141c;
    border: 1px solid #232736;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}

/* === Sliders === */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #1e2230;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: #3b82f6;
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

/* === Player Stem Buttons === */
QPushButton#StemActive {
    background-color: #262e42;
    color: #ffffff;
    border: 1px solid #3b82f6;
    font-weight: 600;
}
QPushButton#StemInactive {
    background-color: #161822;
    color: #8a90a4;
    border: 1px solid #262a38;
}
"""
