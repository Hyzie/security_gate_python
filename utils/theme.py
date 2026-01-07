"""
Futuristic HUD Theme System
Cyberpunk/Sci-Fi Robotics Control Panel Styling

This module provides:
- Color palette definitions (HUDColors)
- Typography helpers (HUDFonts)
- Global QSS theme application (apply_hud_theme)
- Angular/chamfered border utilities

Design Philosophy:
- No rounded corners (border-radius: 0)
- Angular/chamfered edges for technical look
- Neon cyan/electric blue primary accents
- Amber/orange for warnings and alerts
- Deep dark backgrounds (#0b0c10, #1f2833)
- Monospaced fonts for data display
- Glowing effects on interactive elements
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase


class HUDColors:
    """
    Cyberpunk Color Palette - Military/Industrial Robotics Theme
    """
    # Backgrounds
    BG_DARK = "#0b0c10"          # Deep dark background
    BG_DARKER = "#080809"        # Even darker for contrast
    BG_PANEL = "#1f2833"         # Panel/card background
    BG_CARD = "#1a1d24"          # Card background (slightly lighter)
    BG_INPUT = "#15171c"         # Input field background
    
    # Primary Accent (Neon Cyan/Electric Blue)
    PRIMARY = "#66fcf1"          # Bright cyan
    PRIMARY_DIM = "#45a29e"      # Dimmed cyan
    PRIMARY_DARK = "#2a6b6a"     # Dark cyan
    
    # Secondary Accent (Amber/Orange - Warnings)
    SECONDARY = "#ffa500"        # Amber/Orange
    SECONDARY_DIM = "#cc8400"    # Dimmed orange
    
    # Success/Active (Green)
    SUCCESS = "#00ff88"          # Bright green
    SUCCESS_DIM = "#00cc6a"      # Dimmed green
    
    # Error/Alert (Red)
    ERROR = "#ff3366"            # Bright red
    ERROR_DIM = "#cc2952"        # Dimmed red
    
    # Text
    TEXT_PRIMARY = "#e8eef2"     # Light cyan-white
    TEXT_DIM = "#8b9ba8"         # Dimmed text
    TEXT_DISABLED = "#4a5560"    # Disabled text
    
    # Borders
    BORDER = "#2d3b47"           # Border color
    BORDER_DIM = "#1a2229"       # Dimmed border
    BORDER_BRIGHT = "#3a4d5e"    # Bright border
    
    # Hover/Active states
    HOVER_BG = "#252d36"         # Hover background
    ACTIVE_BG = "#2a3540"        # Active background
    
    # Special effects
    GLOW_PRIMARY = "rgba(102, 252, 241, 0.5)"    # Cyan glow
    GLOW_SECONDARY = "rgba(255, 165, 0, 0.5)"    # Orange glow
    GLOW_SUCCESS = "rgba(0, 255, 136, 0.5)"      # Green glow


class HUDFonts:
    """
    Typography system for HUD interface
    Prioritizes monospace/tech fonts for data display
    """
    
    _MONOSPACE_FONTS = [
        "Consolas",
        "Roboto Mono",
        "Courier New",
        "Monaco",
        "Menlo",
        "Monospace"
    ]
    
    _DISPLAY_FONTS = [
        "Segoe UI",
        "Roboto",
        "Arial",
        "Helvetica"
    ]
    
    @staticmethod
    def get_monospace_font(size: int = 10, bold: bool = False) -> QFont:
        """Get monospace font for data display (telemetry style)"""
        available = QFontDatabase.families()
        
        for font_name in HUDFonts._MONOSPACE_FONTS:
            if font_name in available:
                font = QFont(font_name, size)
                font.setBold(bold)
                return font
        
        # Fallback
        font = QFont("Courier", size)
        font.setBold(bold)
        return font
    
    @staticmethod
    def get_display_font(size: int = 10, bold: bool = False) -> QFont:
        """Get display font for headings and UI labels"""
        available = QFontDatabase.families()
        
        for font_name in HUDFonts._DISPLAY_FONTS:
            if font_name in available:
                font = QFont(font_name, size)
                font.setBold(bold)
                return font
        
        # Fallback
        font = QFont("Arial", size)
        font.setBold(bold)
        return font


def apply_hud_theme(app: QApplication):
    """
    Apply global HUD theme to the application
    
    This function sets the application-wide QSS stylesheet
    with cyberpunk/sci-fi styling:
    - Dark backgrounds
    - Angular borders (no rounded corners)
    - Neon cyan/orange accents
    - Glowing hover effects
    - Monospace fonts for data
    
    Args:
        app: QApplication instance
    """
    
    qss = f"""
    /* ========================================================== */
    /* GLOBAL APPLICATION STYLING - CYBERPUNK HUD THEME */
    /* ========================================================== */
    
    QWidget {{
        background-color: {HUDColors.BG_DARK};
        color: {HUDColors.TEXT_PRIMARY};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
        border: none;
    }}
    
    /* ========================================================== */
    /* PUSH BUTTONS - Touch Panel Actuator Style */
    /* ========================================================== */
    
    QPushButton {{
        background-color: {HUDColors.BG_PANEL};
        color: {HUDColors.TEXT_PRIMARY};
        border: 2px solid {HUDColors.BORDER};
        border-radius: 0px;
        padding: 8px 16px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        min-height: 32px;
    }}
    
    QPushButton:hover {{
        background-color: {HUDColors.HOVER_BG};
        border-color: {HUDColors.PRIMARY_DIM};
        color: {HUDColors.PRIMARY};
    }}
    
    QPushButton:pressed {{
        background-color: {HUDColors.ACTIVE_BG};
        border-color: {HUDColors.PRIMARY};
    }}
    
    QPushButton:disabled {{
        background-color: {HUDColors.BG_INPUT};
        border-color: {HUDColors.BORDER_DIM};
        color: {HUDColors.TEXT_DISABLED};
    }}
    
    /* Primary Action Buttons */
    QPushButton#primary,
    QPushButton[class="primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {HUDColors.PRIMARY_DARK},
            stop:1 {HUDColors.PRIMARY_DIM});
        border: 2px solid {HUDColors.PRIMARY};
        color: {HUDColors.BG_DARK};
    }}
    
    QPushButton#primary:hover,
    QPushButton[class="primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {HUDColors.PRIMARY_DIM},
            stop:1 {HUDColors.PRIMARY});
        border-color: {HUDColors.PRIMARY};
        color: {HUDColors.BG_DARK};
    }}
    
    /* ========================================================== */
    /* INPUT FIELDS - Terminal Style */
    /* ========================================================== */
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {HUDColors.BG_INPUT};
        color: {HUDColors.TEXT_PRIMARY};
        border: 1px solid {HUDColors.BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        font-family: 'Consolas', 'Courier New', monospace;
        selection-background-color: {HUDColors.PRIMARY_DIM};
        selection-color: {HUDColors.BG_DARK};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {HUDColors.PRIMARY};
        background-color: {HUDColors.BG_PANEL};
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {HUDColors.BG_DARKER};
        color: {HUDColors.TEXT_DISABLED};
        border-color: {HUDColors.BORDER_DIM};
    }}
    
    /* ========================================================== */
    /* COMBO BOX - Dropdown Selector */
    /* ========================================================== */
    
    QComboBox {{
        background-color: {HUDColors.BG_INPUT};
        color: {HUDColors.TEXT_PRIMARY};
        border: 1px solid {HUDColors.BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        min-height: 30px;
    }}
    
    QComboBox:hover {{
        border-color: {HUDColors.PRIMARY_DIM};
    }}
    
    QComboBox:focus {{
        border-color: {HUDColors.PRIMARY};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {HUDColors.PRIMARY};
        width: 0;
        height: 0;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {HUDColors.BG_PANEL};
        color: {HUDColors.TEXT_PRIMARY};
        border: 2px solid {HUDColors.PRIMARY};
        selection-background-color: {HUDColors.PRIMARY_DIM};
        selection-color: {HUDColors.BG_DARK};
        outline: none;
    }}
    
    /* ========================================================== */
    /* SPIN BOX - Numeric Input */
    /* ========================================================== */
    
    QSpinBox, QDoubleSpinBox {{
        background-color: {HUDColors.BG_INPUT};
        color: {HUDColors.TEXT_PRIMARY};
        border: 1px solid {HUDColors.BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: bold;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {HUDColors.PRIMARY};
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        background-color: {HUDColors.BG_PANEL};
        border-left: 1px solid {HUDColors.BORDER};
        border-bottom: 1px solid {HUDColors.BORDER};
    }}
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {HUDColors.BG_PANEL};
        border-left: 1px solid {HUDColors.BORDER};
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {HUDColors.HOVER_BG};
    }}
    
    /* ========================================================== */
    /* CHECKBOXES AND RADIO BUTTONS */
    /* ========================================================== */
    
    QCheckBox, QRadioButton {{
        color: {HUDColors.TEXT_PRIMARY};
        spacing: 8px;
    }}
    
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {HUDColors.BORDER};
        background-color: {HUDColors.BG_INPUT};
    }}
    
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {HUDColors.PRIMARY_DIM};
    }}
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {HUDColors.PRIMARY};
        border-color: {HUDColors.PRIMARY};
    }}
    
    QRadioButton::indicator {{
        border-radius: 0px;  /* Keep angular for sci-fi look */
    }}
    
    /* ========================================================== */
    /* SCROLL BARS - Minimal Tech Style */
    /* ========================================================== */
    
    QScrollBar:vertical {{
        background-color: {HUDColors.BG_DARKER};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {HUDColors.BORDER_BRIGHT};
        min-height: 30px;
        border-radius: 0px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {HUDColors.PRIMARY_DIM};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {HUDColors.BG_DARKER};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {HUDColors.BORDER_BRIGHT};
        min-width: 30px;
        border-radius: 0px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {HUDColors.PRIMARY_DIM};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* ========================================================== */
    /* LABELS AND TEXT */
    /* ========================================================== */
    
    QLabel {{
        color: {HUDColors.TEXT_PRIMARY};
        background: transparent;
    }}
    
    QLabel[class="title"] {{
        color: {HUDColors.PRIMARY};
        font-size: 14pt;
        font-weight: bold;
        letter-spacing: 2px;
    }}
    
    QLabel[class="subtitle"] {{
        color: {HUDColors.TEXT_DIM};
        font-size: 9pt;
    }}
    
    QLabel[class="monospace"] {{
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: bold;
    }}
    
    /* ========================================================== */
    /* TAB WIDGET - Angular Tabs */
    /* ========================================================== */
    
    QTabWidget::pane {{
        border: 2px solid {HUDColors.BORDER};
        border-radius: 0px;
        background-color: {HUDColors.BG_PANEL};
    }}
    
    QTabBar::tab {{
        background-color: {HUDColors.BG_DARK};
        color: {HUDColors.TEXT_DIM};
        border: 2px solid {HUDColors.BORDER};
        border-bottom: none;
        border-radius: 0px;
        padding: 8px 16px;
        margin-right: 2px;
        font-weight: bold;
        text-transform: uppercase;
    }}
    
    QTabBar::tab:selected {{
        background-color: {HUDColors.BG_PANEL};
        color: {HUDColors.PRIMARY};
        border-color: {HUDColors.PRIMARY};
        border-bottom: 2px solid {HUDColors.BG_PANEL};
    }}
    
    QTabBar::tab:hover {{
        background-color: {HUDColors.HOVER_BG};
        color: {HUDColors.PRIMARY_DIM};
    }}
    
    /* ========================================================== */
    /* GROUP BOX - Panel Container */
    /* ========================================================== */
    
    QGroupBox {{
        border: 2px solid {HUDColors.BORDER};
        border-radius: 0px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
        color: {HUDColors.PRIMARY};
        background-color: {HUDColors.BG_DARK};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* ========================================================== */
    /* PROGRESS BARS - Linear Indicator */
    /* ========================================================== */
    
    QProgressBar {{
        background-color: {HUDColors.BG_INPUT};
        border: 1px solid {HUDColors.BORDER};
        border-radius: 0px;
        height: 20px;
        text-align: center;
        color: {HUDColors.TEXT_PRIMARY};
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: bold;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {HUDColors.PRIMARY_DARK},
            stop:0.5 {HUDColors.PRIMARY},
            stop:1 {HUDColors.PRIMARY_DIM});
        border-radius: 0px;
    }}
    
    /* ========================================================== */
    /* SLIDERS - Angular Control */
    /* ========================================================== */
    
    QSlider::groove:horizontal {{
        background-color: {HUDColors.BG_INPUT};
        height: 6px;
        border: 1px solid {HUDColors.BORDER};
        border-radius: 0px;
    }}
    
    QSlider::handle:horizontal {{
        background-color: {HUDColors.PRIMARY};
        border: 2px solid {HUDColors.PRIMARY};
        width: 16px;
        margin: -6px 0;
        border-radius: 0px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background-color: {HUDColors.PRIMARY_DIM};
    }}
    
    /* ========================================================== */
    /* TOOLTIPS - HUD Info Panels */
    /* ========================================================== */
    
    QToolTip {{
        background-color: {HUDColors.BG_PANEL};
        color: {HUDColors.TEXT_PRIMARY};
        border: 2px solid {HUDColors.PRIMARY};
        border-radius: 0px;
        padding: 6px 10px;
        font-family: 'Consolas', 'Courier New', monospace;
    }}
    
    /* ========================================================== */
    /* MENU BAR AND MENUS */
    /* ========================================================== */
    
    QMenuBar {{
        background-color: {HUDColors.BG_DARKER};
        color: {HUDColors.TEXT_PRIMARY};
        border-bottom: 1px solid {HUDColors.BORDER};
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {HUDColors.HOVER_BG};
        color: {HUDColors.PRIMARY};
    }}
    
    QMenu {{
        background-color: {HUDColors.BG_PANEL};
        color: {HUDColors.TEXT_PRIMARY};
        border: 2px solid {HUDColors.PRIMARY};
        border-radius: 0px;
    }}
    
    QMenu::item {{
        padding: 6px 25px 6px 10px;
    }}
    
    QMenu::item:selected {{
        background-color: {HUDColors.PRIMARY_DIM};
        color: {HUDColors.BG_DARK};
    }}
    
    /* ========================================================== */
    /* STATUS BAR */
    /* ========================================================== */
    
    QStatusBar {{
        background-color: {HUDColors.BG_DARKER};
        color: {HUDColors.TEXT_DIM};
        border-top: 1px solid {HUDColors.BORDER};
    }}
    
    /* ========================================================== */
    /* FRAME - Generic Container */
    /* ========================================================== */
    
    QFrame[frameShape="4"],  /* HLine */
    QFrame[frameShape="5"] {{ /* VLine */
        background-color: {HUDColors.BORDER};
    }}
    """
    
    # Apply stylesheet to application
    app.setStyleSheet(qss)
    
    print("✓ HUD Theme Applied")
    print(f"  Primary: {HUDColors.PRIMARY}")
    print(f"  Secondary: {HUDColors.SECONDARY}")
    print(f"  Background: {HUDColors.BG_DARK}")
