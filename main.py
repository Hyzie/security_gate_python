#!/usr/bin/env python3
"""
RFID Reader Application - Modern Python Edition
Windows 11 Fluent Design Interface

A professional RFID tag reader control application featuring:
- Real-time tag inventory with multi-antenna support
- Sensor-based direction detection (IN/OUT)
- Confidence-based tag detection analysis
- Reader configuration and GPIO control
- Excel data export

Requirements:
    - Python 3.10+
    - PyQt6
    - pyqt6-fluent-widgets
    - pyserial
    - openpyxl (optional, for Excel export)

Usage:
    python main.py

Author: Modernized from legacy C# Windows Forms application
License: MIT
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QFont, QFontDatabase

# High DPI support
if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def setup_fonts():
    """Setup application fonts"""
    # Try to use Segoe UI (Windows 11 default)
    preferred_fonts = ["Segoe UI", "SF Pro Display", "Helvetica Neue", "Arial"]
    
    available_families = QFontDatabase.families()
    
    for font_name in preferred_fonts:
        if font_name in available_families:
            return QFont(font_name, 10)
    
    return QFont("Arial", 10)


def main():
    """Application entry point with Raspberry Pi optimization"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("RFID Reader")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Modern RFID Solutions")
    
    # Set font
    app.setFont(setup_fonts())
    
    # Enable internationalization
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    
    # Import here to avoid circular imports
    from views import MainWindow
    from controllers import ReaderController
    from utils.ui_config import get_ui_config, is_raspberry_pi
    
    # Get responsive UI configuration
    ui_config = get_ui_config()
    
    # Create main window
    window = MainWindow()
    
    # Create controller and connect to window
    controller = ReaderController(window)
    
    # Handle application quit
    app.aboutToQuit.connect(controller.cleanup)
    
    # RASPBERRY PI OPTIMIZATION:
    # - Automatically go fullscreen on small screens (1024x600)
    # - Show window normally on larger screens
    if ui_config.profile == 'small' or is_raspberry_pi():
        window.showFullScreen()
        print(f"✓ Running in fullscreen mode")
        print(f"  Screen: {ui_config.screen_width}x{ui_config.screen_height}")
        print(f"  Profile: {ui_config.profile}")
        print(f"  Raspberry Pi: {is_raspberry_pi()}")
        
        # Disable animations on Pi for better performance
        if is_raspberry_pi():
            app.setEffectEnabled(Qt.UIEffect.AnimateCombo, False)
            app.setEffectEnabled(Qt.UIEffect.AnimateTooltip, False)
            print(f"  Animations: Disabled (Pi optimization)")
    else:
        window.show()
        print(f"✓ Running in windowed mode")
        print(f"  Screen: {ui_config.screen_width}x{ui_config.screen_height}")
        print(f"  Profile: {ui_config.profile}")
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

