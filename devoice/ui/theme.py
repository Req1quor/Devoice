"""Studio-Grade Design System & QSS Generator for Devoice.

Inspired by modern industrial minimalist audio hardware, high-end VST interfaces,
Teenage Engineering, and Linear (Pristine Noir & Blanc).
"""

from __future__ import annotations

from pathlib import Path

_CHECK_SVG_PATH = Path(__file__).resolve().parent.parent / "assets" / "check.svg"
_CHECK_SVG_URL = _CHECK_SVG_PATH.as_posix()


class StudioColors:
    """Design tokens for minimalist studio surfaces, borders, typography, and monochrome accents."""

    # Surfaces (Deep dark graphite / zinc)
    SURFACE_BASE = "#09090B"               # Main chassis (deepest matte black)
    SURFACE_PANEL = "#111114"              # Rack modules, cards
    SURFACE_ELEVATED = "#18181B"           # Hovered cards, elevated modules
    SURFACE_SUNKEN = "#0D0D10"             # Sunken LCDs, inputs, meter grooves
    SURFACE_INTERACTIVE = "#18181B"        # Secondary buttons, controls
    SURFACE_INTERACTIVE_HOVER = "#27272A"  # Button hover
    SURFACE_INTERACTIVE_PRESSED = "#09090B"# Button pressed

    # Borders & Dividers
    BORDER_SUBTLE = "#1E1E24"              # Inner dividers, sunken grooves
    BORDER_DEFAULT = "#27272A"             # Component outlines, chassis edges
    BORDER_METALLIC = "#3F3F46"            # Metallic bezel highlight on hover
    BORDER_FOCUS = "#71717A"               # Neutral focus ring (pure monochrome)

    # Typography & Text
    TEXT_PRIMARY = "#F4F4F5"               # Crisp high-contrast readout
    TEXT_SECONDARY = "#A1A1AA"             # Secondary labels, hints
    TEXT_TERTIARY = "#71717A"              # Deep slate, unit specs
    TEXT_DISABLED = "#52525B"              # Inactive controls
    TEXT_DARK = "#000000"                  # Primary button text on bright fill

    # Monochrome Accents
    ACCENT_WHITE = "#FFFFFF"               # Hero action, active stems, indicators
    ACCENT_WHITE_HOVER = "#E4E4E7"
    ACCENT_WHITE_PRESSED = "#D4D4D8"
    ACCENT_WHITE_DIM = "#27272A"

    # Hardware LED / Status Accents (retained for backward compatibility)
    ACCENT_AMBER = "#F59E0B"
    ACCENT_CYAN = "#00D2FF"
    ACCENT_EMERALD = "#10B981"
    ACCENT_ROSE = "#EF4444"
    ACCENT_ROSE_BG = "#221010"
    ACCENT_ROSE_BORDER = "#451A1A"
    ACCENT_SLATE = "#CBD5E1"


class StudioFonts:
    """Typographic scale and font stacks."""

    FONT_FAMILY_SANS = "'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    FONT_FAMILY_MONO = "'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"


class StudioMetrics:
    """Ergonomic dimensions and curvature."""

    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "8px"
    RADIUS_ROUND = "12px"


def build_studio_theme() -> str:
    """Generate the complete studio-grade QSS theme string in pristine Noir & Blanc."""
    return f"""
/* ==========================================================================
   DEVOICE STUDIO-GRADE WORKSTATION THEME
   Pristine Minimalist Noir & Blanc Aesthetic
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
    letter-spacing: 1.2px;
    color: {StudioColors.ACCENT_WHITE};
    padding-left: 2px;
}}

#DeviceBadge {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 4px 10px;
    font-family: {StudioFonts.FONT_FAMILY_SANS};
    font-size: 11px;
    font-weight: 600;
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
    background-color: {StudioColors.SURFACE_ELEVATED};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
}}

#DropZone[loaded="true"] {{
    background-color: {StudioColors.SURFACE_PANEL};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
}}

#DropZone[loaded="true"]:hover {{
    border-color: {StudioColors.ACCENT_WHITE};
    background-color: {StudioColors.SURFACE_ELEVATED};
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
    font-family: {StudioFonts.FONT_FAMILY_SANS};
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
    selection-background-color: {StudioColors.BORDER_METALLIC};
    selection-color: {StudioColors.TEXT_PRIMARY};
}}

QLineEdit#YouTubeInput:hover {{
    border-color: {StudioColors.BORDER_METALLIC};
}}

QLineEdit#YouTubeInput:focus {{
    border: 1px solid {StudioColors.BORDER_FOCUS};
    background-color: #121216;
}}

QLineEdit#YouTubeInput:disabled {{
    background-color: {StudioColors.SURFACE_SUNKEN};
    color: {StudioColors.TEXT_DISABLED};
    border-color: {StudioColors.BORDER_SUBTLE};
}}

QPushButton#YouTubeButton {{
    background-color: {StudioColors.SURFACE_INTERACTIVE};
    color: {StudioColors.TEXT_PRIMARY};
    border: 1px solid {StudioColors.BORDER_DEFAULT};
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#YouTubeButton:hover {{
    background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
    border-color: {StudioColors.BORDER_METALLIC};
    color: {StudioColors.ACCENT_WHITE};
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
    border: 1px solid {StudioColors.BORDER_FOCUS};
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
    selection-background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
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
    color: {StudioColors.ACCENT_WHITE};
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
    background-color: {StudioColors.SURFACE_INTERACTIVE_HOVER};
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

/* === Tactile Studio Checkboxes (Noir & Blanc Minimalism) === */
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
    border-color: {StudioColors.BORDER_FOCUS};
    background-color: {StudioColors.SURFACE_ELEVATED};
}}

QCheckBox::indicator:checked {{
    background-color: {StudioColors.ACCENT_WHITE};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
    image: url("{_CHECK_SVG_URL}");
}}

QCheckBox::indicator:checked:hover {{
    background-color: {StudioColors.ACCENT_WHITE_HOVER};
    border-color: {StudioColors.ACCENT_WHITE_HOVER};
    image: url("{_CHECK_SVG_URL}");
}}

QCheckBox::indicator:disabled {{
    border-color: {StudioColors.BORDER_SUBTLE};
    background-color: {StudioColors.SURFACE_SUNKEN};
}}

QCheckBox:disabled {{
    color: {StudioColors.TEXT_DISABLED};
}}

/* === Primary Action Button (Pure Crisp White Hero) === */
QPushButton#PrimaryButton {{
    background-color: {StudioColors.ACCENT_WHITE};
    color: {StudioColors.TEXT_DARK};
    border: 1px solid {StudioColors.ACCENT_WHITE};
    border-radius: {StudioMetrics.RADIUS_MD};
    font-size: 13.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    padding: 10px 24px;
    min-height: 22px;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {StudioColors.ACCENT_WHITE_HOVER};
    border-color: {StudioColors.ACCENT_WHITE_HOVER};
    color: #000000;
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {StudioColors.ACCENT_WHITE_PRESSED};
    border-color: {StudioColors.ACCENT_WHITE_PRESSED};
    color: #000000;
}}

QPushButton#PrimaryButton:disabled {{
    background-color: {StudioColors.SURFACE_PANEL};
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
    background-color: {StudioColors.ACCENT_WHITE};
    border-radius: 3px;
}}

/* === Status Console Readout === */
#StatusLabel, QLabel#StatusLabel {{
    color: {StudioColors.TEXT_SECONDARY};
    font-family: {StudioFonts.FONT_FAMILY_SANS};
    font-size: 11.5px;
    font-weight: 500;
    letter-spacing: 0.2px;
}}

/* === AudioPreviewPlayer (Studio Console) === */
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
    font-family: {StudioFonts.FONT_FAMILY_SANS};
    font-size: 11.5px;
    font-weight: 600;
    color: {StudioColors.TEXT_PRIMARY};
}}

/* Precision Scrubber Slider */
QSlider::groove:horizontal {{
    height: 4px;
    background-color: {StudioColors.SURFACE_SUNKEN};
    border: 1px solid {StudioColors.BORDER_SUBTLE};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background-color: {StudioColors.ACCENT_WHITE};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {StudioColors.ACCENT_WHITE};
    border: 1px solid {StudioColors.BORDER_METALLIC};
    width: 12px;
    height: 12px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 6px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {StudioColors.ACCENT_WHITE};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
}}

/* Transport Play Button */
QPushButton#PlayButton {{
    background-color: {StudioColors.ACCENT_WHITE};
    color: {StudioColors.TEXT_DARK};
    border: 1px solid {StudioColors.ACCENT_WHITE};
    font-weight: 700;
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 6px 16px;
}}

QPushButton#PlayButton:hover {{
    background-color: {StudioColors.ACCENT_WHITE_HOVER};
    border-color: {StudioColors.ACCENT_WHITE_HOVER};
}}

QPushButton#PlayButton:pressed {{
    background-color: {StudioColors.ACCENT_WHITE_PRESSED};
}}

/* Stem Switchers */
QPushButton#StemActive {{
    background-color: {StudioColors.ACCENT_WHITE};
    color: {StudioColors.TEXT_DARK};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
    font-weight: 700;
    border-radius: {StudioMetrics.RADIUS_MD};
    padding: 5px 14px;
}}

QPushButton#StemActive[stem="vocals"],
QPushButton#StemActive[stem="instru"],
QPushButton#StemActive[stem="original"] {{
    background-color: {StudioColors.ACCENT_WHITE};
    border: 1.5px solid {StudioColors.ACCENT_WHITE};
    color: {StudioColors.TEXT_DARK};
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
"""
