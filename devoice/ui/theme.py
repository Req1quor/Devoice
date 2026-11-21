"""Studio-Grade Design System & QSS Generator for Devoice.

Inspired by modern industrial audio hardware, high-end VST interfaces,
Teenage Engineering, and Linear.
"""

from __future__ import annotations


class StudioColors:
    """Design tokens for studio surfaces, borders, typography, and hardware accents."""

    # Surfaces
    SURFACE_BASE = "#111215"               # Main chassis
    SURFACE_PANEL = "#16181D"              # Rack modules, cards
    SURFACE_ELEVATED = "#1D2027"           # Hovered cards, elevated modules
    SURFACE_SUNKEN = "#0D0E11"             # Sunken LCDs, inputs, meter grooves
    SURFACE_INTERACTIVE = "#222631"        # Buttons, secondary controls
    SURFACE_INTERACTIVE_HOVER = "#2B303E"  # Button hover
    SURFACE_INTERACTIVE_PRESSED = "#171A21"# Button pressed

    # Borders & Dividers
    BORDER_SUBTLE = "#232733"              # Inner dividers, sunken grooves
    BORDER_DEFAULT = "#2D3342"             # Component outlines, chassis edges
    BORDER_METALLIC = "#3D4457"            # Metallic bezel highlight
    BORDER_FOCUS = "#00D2FF"               # Focus ring

    # Typography & Text
    TEXT_PRIMARY = "#F1F5F9"               # Crisp high-contrast readout
    TEXT_SECONDARY = "#94A3B8"             # Secondary labels, hints
    TEXT_TERTIARY = "#64748B"              # Deep slate, unit specs
    TEXT_DISABLED = "#475569"              # Inactive controls
    TEXT_DARK = "#0B0C10"                  # Primary button text on bright fill

    # Studio Hardware Accents & LED Illumination
    ACCENT_AMBER = "#F59E0B"               # Vocal stem, Hero action
    ACCENT_AMBER_HOVER = "#FBBF24"
    ACCENT_AMBER_PRESSED = "#D97706"
    ACCENT_AMBER_DIM = "#2A1F0E"           # Subtle amber module glow

    ACCENT_CYAN = "#00D2FF"                # Instrumental stem, focus ring, meter start
    ACCENT_CYAN_DIM = "#0C2430"            # Subtle cyan module glow

    ACCENT_EMERALD = "#10B981"             # DSP active LED, GPU hardware status
    ACCENT_EMERALD_DIM = "#0F281E"

    ACCENT_ROSE = "#EF4444"                # Cancel action, alerts
    ACCENT_ROSE_BG = "#241416"
    ACCENT_ROSE_BORDER = "#7F1D1D"

    ACCENT_SLATE = "#CBD5E1"               # Original mix stem
    ACCENT_SLATE_DIM = "#202531"


class StudioFonts:
    """Typographic scale and font stacks."""

    FONT_FAMILY_SANS = "'Segoe UI', 'Inter', -apple-system, sans-serif"
    FONT_FAMILY_MONO = "'Consolas', 'Cascadia Code', 'JetBrains Mono', monospace"


class StudioMetrics:
    """Ergonomic dimensions and curvature."""

    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "8px"
    RADIUS_ROUND = "12px"


def build_studio_theme() -> str:
    """Generate the complete studio-grade QSS theme string."""
    return f"""
/* ==========================================================================
   DEVOICE STUDIO-GRADE WORKSTATION THEME
   Industrial Hardware & VST Aesthetic
   ========================================================================== */

/* === Global Application Root === */
QMainWindow {{
    background-color: {StudioColors.SURFACE_BASE};
}}

QWidget {{
    color: {StudioColors.TEXT_PRIMARY};
    font-family: {StudioFonts.FONT_FAMILY_SANS};
    font-size: 12px;
}}

QWidget:focus {{
    outline: none;
}}

QLabel, QCheckBox {{
    background: transparent;
}}

/* === Header & Brand === */
#TitleLabel {{
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: {StudioColors.TEXT_PRIMARY};
    padding-left: 2px;
}}

#DeviceBadge {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 4px 10px;
    font-family: {StudioFonts.FONT_FAMILY_MONO};
    font-size: 11px;
    font-weight: 700;
    color: {StudioColors.TEXT_SECONDARY};
}}

/* === Drop Zone (Audio Cartridge Ingest) === */
#DropZone {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1.5px dashed {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_LG};
    min-height: 112px;
}}

#DropZone:hover {{
    border-color: {StudioColors.BORDER_METALLIC};
    background-color: {StudioColors.SURFACE_ELEVATED};
}}

#DropZone[dragOver="true"] {{
    background-color: #1F1E19;
    border: 1.5px solid {StudioColors.ACCENT_AMBER};
}}

#DropZone[loaded="true"] {{
    background-color: #151821;
    border: 1.5px solid {StudioColors.BORDER_METALLIC};
}}

#DropZone[loaded="true"]:hover {{
    border-color: {StudioColors.ACCENT_CYAN};
    background-color: #191E2B;
}}

#DropZoneTitle {{
    font-size: 13.5px;
    font-weight: 700;
    color: {StudioColors.TEXT_PRIMARY};
}}

#DropZoneSubtitle {{
    font-size: 11.5px;
    color: {StudioColors.TEXT_SECONDARY};
}}

#DropZoneFormats {{
    font-family: {StudioFonts.FONT_FAMILY_MONO};
    font-size: 10.5px;
    letter-spacing: 0.5px;
    color: {StudioColors.TEXT_TERTIARY};
}}

/* === YouTube Stream Ingest Bar === */
QLineEdit#YouTubeInput {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 7px 12px;
    font-size: 12px;
    selection-background-color: {StudioColors.SURFACE_INTERACTIVE};
    selection-color: {StudioColors.TEXT_PRIMARY};
}}

QLineEdit#YouTubeInput:hover {{
    border-color: {StudioColors.BORDER_METALLIC};
}}

QLineEdit#YouTubeInput:focus {{
    border: 1px solid {StudioColors.ACCENT_CYAN};
    background-color: #0E1217;
}}

QLineEdit#YouTubeInput:disabled {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    color: {StudioColors.TEXT_DISABLED};
    border-color: {StudioColors.BORDER_SUBTLE};
}}

QPushButton#YouTubeButton {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1px solid {StudioColors.BORDER_METALLIC};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#YouTubeButton:hover {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
    border-color: #4D566D;
}}

QPushButton#YouTubeButton:pressed {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_PRESSED};
}}

QPushButton#YouTubeButton:disabled {{
    background-color: {StudioColors.SURFACE_PANEL};
    color: {StudioColors.TEXT_DISABLED};
    border-color: {StudioColors.BORDER_SUBTLE};
}}

/* === Multi-File Queue === */
QListWidget {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 4px;
    color: {StudioColors.TEXT_SECONDARY};
    font-family: {StudioFonts.FONT_FAMILY_MONO};
    font-size: 11px;
}}

QListWidget::item {{
    padding: 3px 6px;
    border-radius: {StudioMetrics.RADIUS_SM};
}}

QListWidget::item:selected {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
}}

/* === Cards & Rack Enclosures === */
#SettingsCard, #PlayerCard {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_LG};
}}

/* === Combo Boxes & Dropdowns === */
QLabel {{
    color: {StudioColors.TEXT_SECONDARY};
    font-size: 12px;
}}

QComboBox {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 6px 12px;
    color: {StudioColors.TEXT_PRIMARY};
    font-size: 12px;
    font-weight: 600;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {StudioColors.BORDER_METALLIC};
}}

QComboBox:focus {{
    border: 1px solid {StudioColors.ACCENT_CYAN};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}}

QComboBox::down-arrow {{
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {StudioColors.TEXT_SECONDARY};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1px solid {StudioColors.BORDER_METALLIC};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 4px;
    color: {StudioColors.TEXT_PRIMARY};
    selection-background-color: {StudioColors.SURFACE_INTERACTIVE};
    selection-color: {StudioColors.TEXT_PRIMARY};
}}

/* === Standard Buttons === */
QPushButton {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
    border-color: {StudioColors.BORDER_METALLIC};
}}

QPushButton:pressed {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_PRESSED};
}}

QPushButton:disabled {{
    background-color: {StudioColors.SURFACE_PANEL};
    color: {StudioColors.TEXT_DISABLED};
    border-color: {StudioColors.BORDER_SUBTLE};
}}

/* === Collapsible Options Drawer Toggle Button === */
#OptionsDrawerButton, QPushButton#OptionsDrawerButton {{
    background-color: {StudioColors.SURFACE_ELEVATED};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    color: {StudioColors.TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: {StudioMetrics.RADIUS_MD};
}}

#OptionsDrawerButton:hover, QPushButton#OptionsDrawerButton:hover {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    border-color: {StudioColors.BORDER_METALLIC};
    color: {StudioColors.TEXT_PRIMARY};
}}

/* === Recessed DSP Drawer Enclosure === */
#DrawerContainer {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 8px 12px;
}}

/* === Tactile Studio Checkboxes (Hardware Rocker Switch Look) === */
QCheckBox {{
    color: {StudioColors.TEXT_PRIMARY};
    font-size: 12px;
    spacing: 8px;
    background: transparent;
}}

QCheckBox:hover {{
    color: #FFFFFF;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1.5px solid {StudioColors.BORDER_METALLIC};
    background-color: {StudioColors.SURFACE_PANEL};
}}

QCheckBox::indicator:hover {{
    border-color: {StudioColors.TEXT_SECONDARY};
    background-color: {StudioColors.SURFACE_ELEVATED};
}}

QCheckBox::indicator:checked {{
    background-color: {StudioColors.ACCENT_AMBER};
    border: 1.5px solid {StudioColors.ACCENT_AMBER};
    image: none;
}}

QCheckBox::indicator:checked:hover {{
    background-color: {StudioColors.ACCENT_AMBER_HOVER};
    border-color: {StudioColors.ACCENT_AMBER_HOVER};
}}

QCheckBox::indicator:disabled {{
    border-color: {StudioColors.BORDER_SUBTLE};
    background-color: {StudioColors.SURFACE_SUNKEN};
}}

QCheckBox:disabled {{
    color: {StudioColors.TEXT_DISABLED};
}}

/* === Primary Action Button (Tactile Studio Amber Hero) === */
QPushButton#PrimaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {StudioColors.ACCENT_AMBER_HOVER}, stop:1 {StudioColors.ACCENT_AMBER_PRESSED});
    color: {StudioColors.TEXT_DARK};
    border: 1px solid {StudioColors.ACCENT_AMBER};
    border-radius: {StudioMetrics.RADIUS_MD};
    font-size: 13.5px;
    font-weight: 800;
    letter-spacing: 0.8px;
    padding: 10px 24px;
    min-height: 22px;
}}

QPushButton#PrimaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FCD34D, stop:1 {StudioColors.ACCENT_AMBER});
    border-color: #FDE68A;
    color: #000000;
}}

QPushButton#PrimaryButton:pressed {{
    background-color: #B45309;
    border-color: #92400E;
    color: #000000;
}}

QPushButton#PrimaryButton:disabled {{
    background: {StudioColors.SURFACE_PANEL};
    color: {StudioColors.TEXT_DISABLED};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
}}

/* === Cancel Button === */
QPushButton#CancelButton {{
    background-color: {StudioColors.ACCENT_ROSE_BG};
    color: #FCA5A5;
    border: 1px solid {StudioColors.ACCENT_ROSE_BORDER};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 8px 16px;
    font-weight: 700;
}}

QPushButton#CancelButton:hover {{
    background-color: #38161A;
    border-color: {StudioColors.ACCENT_ROSE};
    color: #FFFFFF;
}}

QPushButton#CancelButton:pressed {{
    background-color: #1E0E10;
}}

/* === Progress Meter === */
QProgressBar {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: {StudioMetrics.RADIUS_SM};
    height: 7px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {StudioColors.ACCENT_CYAN}, stop:1 {StudioColors.ACCENT_AMBER});
    border-radius: 3px;
}}

/* === Status Console Readout === */
#StatusLabel, QLabel#StatusLabel {{
    color: {StudioColors.TEXT_SECONDARY};
    font-family: {StudioFonts.FONT_FAMILY_MONO};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
}}

/* === AudioPreviewPlayer (Studio VST Console) === */
#PlayerTrackLabel {{
    font-family: {StudioFonts.FONT_FAMILY_SANS};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.0px;
    color: {StudioColors.TEXT_SECONDARY};
}}

#PlayerTimeLabel {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: {StudioMetrics.RADIUS_SM};
    padding: 3px 8px;
    font-family: {StudioFonts.FONT_FAMILY_MONO};
    font-size: 11.5px;
    font-weight: 700;
    color: {StudioColors.TEXT_PRIMARY};
}}

/* Precision Aluminum Scrubber Slider */
QSlider::groove:horizontal {{
    height: 5px;
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background-color: {StudioColors.ACCENT_CYAN};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {StudioColors.TEXT_PRIMARY};
    border: 1.5px solid {StudioColors.BORDER_METALLIC};
    width: 13px;
    height: 13px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 6.5px;
}}

QSlider::handle:horizontal:hover {{
    background-color: #FFFFFF;
    border: 1.5px solid {StudioColors.ACCENT_CYAN};
}}

/* Transport Play Button */
QPushButton#PlayButton {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1px solid {StudioColors.BORDER_METALLIC};
    font-weight: 700;
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 6px 16px;
}}

QPushButton#PlayButton:hover {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
    border-color: #4D566D;
}}

QPushButton#PlayButton:pressed {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_PRESSED};
}}

/* Stem Switchers */
QPushButton#StemActive {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1.5px solid {StudioColors.TEXT_PRIMARY};
    font-weight: 700;
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 5px 14px;
}}

QPushButton#StemInactive {{
    background-color: {StudioColors.SURFACE_PANEL};
    color: {StudioColors.TEXT_SECONDARY};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    font-weight: 600;
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 5px 14px;
}}

QPushButton#StemInactive:hover {{
    background-color: {StudioColors.SURFACE_ELEVATED};
    border-color: {StudioColors.BORDER_METALLIC};
    color: {StudioColors.TEXT_PRIMARY};
}}

/* Dedicated Stem Color Coding */
QPushButton#StemActive[stem="vocals"] {{
    background-color: {StudioColors.ACCENT_AMBER_DIM};
    border: 1.5px solid {StudioColors.ACCENT_AMBER};
    color: #FCD34D;
}}

QPushButton#StemActive[stem="instru"] {{
    background-color: {StudioColors.ACCENT_CYAN_DIM};
    border: 1.5px solid {StudioColors.ACCENT_CYAN};
    color: #7DD3FC;
}}

QPushButton#StemActive[stem="original"] {{
    background-color: {StudioColors.ACCENT_SLATE_DIM};
    border: 1.5px solid {StudioColors.ACCENT_SLATE};
    color: {StudioColors.TEXT_PRIMARY};
}}
"""
