"""
UI Configuration Module - Responsive Design for Multiple Screen Sizes
Optimized for Raspberry Pi 7" Touchscreen (1024x600)

This module provides screen-aware configuration values that adapt
UI elements based on the detected screen resolution.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize


class UIConfig:
    """
    Responsive UI configuration based on screen size
    
    Profiles:
    - SMALL: 1024x600 (Raspberry Pi 7" touchscreen)
    - MEDIUM: 1280x720 
    - LARGE: 1920x1080 (Original desktop design)
    """
    
    # Screen size thresholds
    SMALL_SCREEN_WIDTH = 1024
    MEDIUM_SCREEN_WIDTH = 1280
    
    def __init__(self):
        """Initialize configuration based on primary screen size"""
        self._detect_screen_size()
        self._configure_ui_values()
    
    def _detect_screen_size(self):
        """Detect screen resolution and set profile"""
        app = QApplication.instance()
        if app is None:
            # Fallback if called before QApplication is created
            self.screen_width = 1024
            self.screen_height = 600
            self.profile = 'small'
            return
        
        screen = app.primaryScreen()
        geometry = screen.availableGeometry()
        
        self.screen_width = geometry.width()
        self.screen_height = geometry.height()
        
        # Determine profile
        if self.screen_width <= self.SMALL_SCREEN_WIDTH:
            self.profile = 'small'
        elif self.screen_width <= self.MEDIUM_SCREEN_WIDTH:
            self.profile = 'medium'
        else:
            self.profile = 'large'
        
        # Raspberry Pi specific detection
        self.is_raspberry_pi = sys.platform.startswith('linux') and \
                              os.path.exists('/proc/device-tree/model')
    
    def _configure_ui_values(self):
        """Set UI values based on screen profile"""
        
        # ============================================================
        # WINDOW SIZING
        # ============================================================
        if self.profile == 'small':
            self.window_width = 1024
            self.window_height = 600
            self.min_width = 1024
            self.min_height = 600
        elif self.profile == 'medium':
            self.window_width = 1280
            self.window_height = 720
            self.min_width = 1024
            self.min_height = 600
        else:  # large
            self.window_width = 1280
            self.window_height = 800
            self.min_width = 1024
            self.min_height = 700
        
        # ============================================================
        # MARGINS & SPACING
        # ============================================================
        if self.profile == 'small':
            self.page_margin_h = 12  # Horizontal margin (was 36)
            self.page_margin_v = 8   # Vertical margin (was 16-20)
            self.card_margin = 10    # Card internal margin (was 20)
            self.card_spacing = 8    # Space between cards (was 12-20)
            self.layout_spacing = 6  # General layout spacing (was 12-16)
        elif self.profile == 'medium':
            self.page_margin_h = 24
            self.page_margin_v = 12
            self.card_margin = 16
            self.card_spacing = 12
            self.layout_spacing = 10
        else:  # large
            self.page_margin_h = 36
            self.page_margin_v = 16
            self.card_margin = 20
            self.card_spacing = 16
            self.layout_spacing = 12
        
        # ============================================================
        # FONTS
        # ============================================================
        if self.profile == 'small':
            self.font_page_title = 16      # Was 22-24
            self.font_card_title = 12      # Was 14
            self.font_body = 9             # Was 10
            self.font_caption = 8          # Was 9
            self.font_stats_value = 18     # Was 20
        elif self.profile == 'medium':
            self.font_page_title = 18
            self.font_card_title = 13
            self.font_body = 10
            self.font_caption = 9
            self.font_stats_value = 20
        else:  # large
            self.font_page_title = 22
            self.font_card_title = 14
            self.font_body = 10
            self.font_caption = 10
            self.font_stats_value = 20
        
        # ============================================================
        # COMPONENT HEIGHTS (Touch-friendly minimum 36px)
        # ============================================================
        if self.profile == 'small':
            self.button_height = 36        # Touch-friendly (was 34-40)
            self.toolbar_height = 44       # Compact toolbar (was 56)
            self.stats_card_height = 56    # Compact stats (was 70)
            self.logo_height = 80          # Bigger logo for visibility
            self.input_row_height = 36     # Input fields (was 40+)
        elif self.profile == 'medium':
            self.button_height = 38
            self.toolbar_height = 50
            self.stats_card_height = 64
            self.logo_height = 100
            self.input_row_height = 40
        else:  # large
            self.button_height = 40
            self.toolbar_height = 56
            self.stats_card_height = 70
            self.logo_height = 120
            self.input_row_height = 40
        
        # ============================================================
        # ICON SIZES
        # ============================================================
        if self.profile == 'small':
            self.icon_title = 16      # Header icons (was 24)
            self.icon_small = 14      # Small icons (was 16-20)
        else:
            self.icon_title = 24
            self.icon_small = 20
        
        # ============================================================
        # NAVIGATION BAR
        # ============================================================
        if self.profile == 'small':
            self.nav_width_compact = 48   # Collapsed nav (icons only)
            self.nav_width_expanded = 160 # Expanded nav (was 200+)
        else:
            self.nav_width_compact = 48
            self.nav_width_expanded = 200
        
        # ============================================================
        # RESPONSIVE FEATURES
        # ============================================================
        # Use scroll areas on small screens for pages with lots of content
        self.use_scroll_area = (self.profile == 'small')
        
        # Collapse navigation by default on small screens
        self.nav_collapsed_default = (self.profile == 'small')
        
        # Show logo on all screens including small
        self.show_logo_in_header = True
        
        # Reduce table row heights on small screens
        if self.profile == 'small':
            self.table_row_height = 32
        else:
            self.table_row_height = 40


# Singleton instance
_config_instance = None


def get_ui_config() -> UIConfig:
    """Get the singleton UI configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = UIConfig()
    return _config_instance


# Convenience function for quick access
def is_small_screen() -> bool:
    """Check if running on small screen (1024x600)"""
    return get_ui_config().profile == 'small'


def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi"""
    import os
    return sys.platform.startswith('linux') and \
           os.path.exists('/proc/device-tree/model')


if __name__ == "__main__":
    # Test configuration
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # For testing without display
    app = QApplication([])
    
    config = get_ui_config()
    print(f"Screen Profile: {config.profile}")
    print(f"Screen Size: {config.screen_width}x{config.screen_height}")
    print(f"Window Size: {config.window_width}x{config.window_height}")
    print(f"Page Title Font: {config.font_page_title}px")
    print(f"Button Height: {config.button_height}px")
    print(f"Use Scroll Area: {config.use_scroll_area}")
    print(f"Raspberry Pi: {config.is_raspberry_pi}")
