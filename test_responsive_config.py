#!/usr/bin/env python3
"""
Test script to verify responsive UI configuration
Run this to check if your screen is correctly detected
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from utils.ui_config import get_ui_config, is_raspberry_pi, is_small_screen


def main():
    """Test the UI configuration detection"""
    
    # Create a minimal QApplication for screen detection
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("RFID Reader App - Responsive UI Configuration Test")
    print("=" * 60)
    
    # Get configuration
    config = get_ui_config()
    
    print(f"\n📱 SCREEN DETECTION:")
    print(f"   Resolution: {config.screen_width}x{config.screen_height}")
    print(f"   Profile: {config.profile.upper()}")
    print(f"   Raspberry Pi: {'YES ✓' if is_raspberry_pi() else 'NO'}")
    print(f"   Small Screen: {'YES ✓' if is_small_screen() else 'NO'}")
    
    print(f"\n🪟 WINDOW SIZING:")
    print(f"   Default Window: {config.window_width}x{config.window_height}")
    print(f"   Minimum Size: {config.min_width}x{config.min_height}")
    
    print(f"\n📐 LAYOUT PARAMETERS:")
    print(f"   Page Margins (H): {config.page_margin_h}px")
    print(f"   Page Margins (V): {config.page_margin_v}px")
    print(f"   Card Margin: {config.card_margin}px")
    print(f"   Card Spacing: {config.card_spacing}px")
    print(f"   Layout Spacing: {config.layout_spacing}px")
    
    print(f"\n✏️  FONTS:")
    print(f"   Page Title: {config.font_page_title}px")
    print(f"   Card Title: {config.font_card_title}px")
    print(f"   Body Text: {config.font_body}px")
    print(f"   Caption: {config.font_caption}px")
    print(f"   Stats Value: {config.font_stats_value}px")
    
    print(f"\n🔲 COMPONENT HEIGHTS:")
    print(f"   Button: {config.button_height}px")
    print(f"   Toolbar: {config.toolbar_height}px")
    print(f"   Stats Card: {config.stats_card_height}px")
    print(f"   Input Row: {config.input_row_height}px")
    print(f"   Logo: {config.logo_height}px")
    
    print(f"\n🎨 UI FEATURES:")
    print(f"   Use Scroll Areas: {'YES ✓' if config.use_scroll_area else 'NO'}")
    print(f"   Nav Collapsed Default: {'YES ✓' if config.nav_collapsed_default else 'NO'}")
    print(f"   Show Logo in Header: {'YES ✓' if config.show_logo_in_header else 'NO'}")
    print(f"   Table Row Height: {config.table_row_height}px")
    
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    if config.profile == 'small':
        print("   ✓ Running in COMPACT mode for 1024x600")
        print("   ✓ Logo hidden to save space")
        print("   ✓ Navigation collapsed by default")
        print("   ✓ Scroll areas enabled for long pages")
        print("   ✓ Touch-friendly button sizes (36px+)")
        if is_raspberry_pi():
            print("   ✓ Raspberry Pi detected - animations will be disabled")
    elif config.profile == 'medium':
        print("   ✓ Running in MEDIUM mode for 1280x720")
        print("   ✓ Balanced layout with moderate spacing")
    else:
        print("   ✓ Running in LARGE mode for 1920x1080")
        print("   ✓ Original desktop design with full spacing")
    
    print("\n" + "=" * 60)
    print("✓ Configuration test complete!")
    print("=" * 60)
    
    # Calculate space savings for small screen
    if config.profile == 'small':
        # Original desktop values
        desktop_page_margin_v = 16
        desktop_page_margin_h = 36
        desktop_title_font = 22
        desktop_stats_height = 70
        desktop_logo_height = 100
        
        # Calculate savings
        margin_save = (desktop_page_margin_h - config.page_margin_h) * 2  # Both sides
        margin_save += (desktop_page_margin_v - config.page_margin_v) * 2  # Top and bottom
        title_save = (desktop_title_font - config.font_page_title) * 2  # Approx line height
        stats_save = (desktop_stats_height - config.stats_card_height) * 3  # 3 stats cards
        logo_save = desktop_logo_height if not config.show_logo_in_header else 0
        
        total_save = margin_save + title_save + stats_save + logo_save
        
        print(f"\n💾 SPACE SAVINGS FOR 1024x600:")
        print(f"   Margins: ~{margin_save}px")
        print(f"   Title: ~{title_save}px")
        print(f"   Stats Cards: ~{stats_save}px")
        print(f"   Logo: ~{logo_save}px")
        print(f"   ───────────────────")
        print(f"   TOTAL: ~{total_save}px saved vertically!")
        print(f"   \n   Original height needed: ~700px")
        print(f"   Optimized height: ~{700 - total_save}px")
        print(f"   Available height: 600px")
        print(f"   Status: {'✓ FITS!' if (700 - total_save) <= 600 else '⚠ May need scrolling'}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
