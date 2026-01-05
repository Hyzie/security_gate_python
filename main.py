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
    """Application entry point"""
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
    
    # Create main window
    window = MainWindow()
    
    # Create controller and connect to window
    controller = ReaderController(window)
    
    # Handle application quit
    app.aboutToQuit.connect(controller.cleanup)
    
    # Show window maximized (fullscreen with taskbar visible)
    window.showMaximized()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

