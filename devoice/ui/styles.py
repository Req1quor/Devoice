"""Dark theme QSS stylesheet for the Devoice application."""

DARK_THEME: str = """
/* ===== Global ===== */
QMainWindow {
    background-color: #0d0d0d;
    font-family: "Segoe UI", sans-serif;
}

QWidget {
    background-color: #0d0d0d;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a4e;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #252545;
    border-color: #7c3aed;
}

QPushButton:pressed {
    background-color: #7c3aed;
    color: #ffffff;
}

QPushButton:disabled {
    background-color: #111122;
    color: #555555;
    border-color: #1a1a2e;
}

QPushButton#StartButton {
    background-color: #7c3aed;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 15px;
    font-weight: 700;
}

QPushButton#StartButton:hover {
    background-color: #9333ea;
}

QPushButton#StartButton:pressed {
    background-color: #a855f7;
}

QPushButton#StartButton:disabled {
    background-color: #2a2a4e;
    color: #555555;
}

/* ===== Progress Bar ===== */
QProgressBar {
    background-color: #1a1a2e;
    border: 1px solid #2a2a4e;
    border-radius: 8px;
    text-align: center;
    color: #e0e0e0;
    font-size: 12px;
    min-height: 22px;
    max-height: 22px;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed,
        stop:0.5 #9333ea,
        stop:1 #a855f7
    );
    border-radius: 7px;
}

/* ===== List Widget ===== */
QListWidget {
    background-color: #1a1a2e;
    border: 1px solid #2a2a4e;
    border-radius: 8px;
    padding: 4px;
    color: #e0e0e0;
    font-size: 12px;
    outline: none;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #7c3aed;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #252545;
}

/* ===== ComboBox ===== */
QComboBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a4e;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #7c3aed;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #2a2a4e;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: #1a1a2e;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #a855f7;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    border: 1px solid #7c3aed;
    border-radius: 8px;
    color: #e0e0e0;
    selection-background-color: #7c3aed;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* ===== Slider ===== */
QSlider::groove:horizontal {
    background-color: #1a1a2e;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #a855f7;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background-color: #9333ea;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed,
        stop:1 #a855f7
    );
    border-radius: 3px;
}

/* ===== Labels ===== */
QLabel#TitleLabel {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    background: transparent;
}

QLabel#SubtitleLabel {
    font-size: 12px;
    color: #6666aa;
    background: transparent;
}

QLabel#StatusLabel {
    font-size: 12px;
    color: #8888aa;
    background: transparent;
}

QLabel#DeviceLabel {
    font-size: 12px;
    color: #4ade80;
    font-weight: 600;
    background: transparent;
}

/* ===== Drop Zone ===== */
QWidget#DropZone {
    background-color: #1a1a2e;
    border: 2px dashed #2a2a4e;
    border-radius: 12px;
}

QWidget#DropZone:hover {
    border-color: #7c3aed;
    background-color: #1e1e38;
}

/* ===== Scrollbar ===== */
QScrollBar:vertical {
    background-color: #0d0d0d;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2a2a4e;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #7c3aed;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
    border: none;
    height: 0;
}
"""
