#!/usr/bin/env python3
"""
Test launcher to simulate Raspberry Pi 7" screen on Windows
Forces 1024x600 resolution and small profile
"""

import sys
import os

# Add project root to path
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
    preferred_fonts = ["Segoe UI", "SF Pro Display", "Helvetica Neue", "Arial"]
    available_families = QFontDatabase.families()
    
    for font_name in preferred_fonts:
        if font_name in available_families:
            return QFont(font_name, 10)
    
    return QFont("Arial", 10)


def main():
    """Application entry point - SIMULATING RASPBERRY PI 7\" SCREEN"""
    
    print("=" * 60)
    print("🧪 TEST MODE: Simulating Raspberry Pi 7\" Screen (1024x600)")
    print("=" * 60)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("RFID Reader - TEST MODE")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Modern RFID Solutions")
    
    # Set font
    app.setFont(setup_fonts())
    
    # Enable internationalization
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    
    # Import UI config and FORCE small profile
    from utils.ui_config import UIConfig
    
    # Create a custom config instance for testing
    test_config = UIConfig()
    test_config.screen_width = 1024
    test_config.screen_height = 600
    test_config.profile = 'small'
    test_config._configure_ui_values()
    
    print(f"✓ Forcing small profile")
    print(f"✓ Window will be: {test_config.window_width}x{test_config.window_height}")
    print(f"✓ Fonts scaled down: Title={test_config.font_page_title}px")
    print(f"✓ Buttons: {test_config.button_height}px height")
    print(f"✓ Logo hidden: {not test_config.show_logo_in_header}")
    print("=" * 60)
    print()
    
    # Override the singleton
    import utils.ui_config
    utils.ui_config._config_instance = test_config
    
    # Import here to avoid circular imports
    from views import MainWindow
    from controllers import ReaderController
    
    # Create main window
    window = MainWindow()
    
    # Force 1024x600 window size (non-fullscreen for testing)
    window.resize(1024, 600)
    window.setMaximumSize(1024, 600)  # Prevent manual resizing
    
    # Create controller
    controller = ReaderController(window)
    
    # Handle application quit
    app.aboutToQuit.connect(controller.cleanup)
    
    # Show window (not fullscreen for easier testing)
    window.show()
    
    print("🎯 Testing Tips:")
    print("   1. Check if all content fits vertically (600px)")
    print("   2. Verify no horizontal scrolling")
    print("   3. Test if buttons are large enough to click")
    print("   4. Check if text is readable")
    print("   5. Navigate through all pages")
    print("   6. Try the Settings page (should have scroll area)")
    print()
    print("Press Ctrl+C or close window to exit")
    print()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
