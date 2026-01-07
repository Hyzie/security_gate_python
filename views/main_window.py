"""
Main Window - Windows 11 Fluent Design
Modern RFID Reader Application Interface
"""

import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QFrame, QSplitter, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap

from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition,
    FluentIcon as FIF, setTheme, Theme, setThemeColor,
    NavigationPushButton, NavigationAvatarWidget
)
from qfluentwidgets import qconfig

from .inventory_page import InventoryPage
from .settings_page import SettingsPage
from .connection_page import ConnectionPage
from .gpio_page import GPIOPage

# Import responsive UI configuration
from utils.ui_config import get_ui_config


class MainWindow(FluentWindow):
    """
    Main application window with Fluent Design navigation
    """
    
    # Signals for controller communication
    connect_reader_requested = pyqtSignal(str, int)  # port, baudrate
    disconnect_reader_requested = pyqtSignal()
    start_inventory_requested = pyqtSignal(dict)  # antenna config
    stop_inventory_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Prepare theme-aware logo paths
        self.nav_logo_widget = None
        self.logo_path = self._current_logo_path()
        
        # Get responsive UI configuration
        self.ui_config = get_ui_config()
        
        # Window setup with responsive sizing
        self.setWindowTitle("RFID Reader - Modern Interface")
        self.resize(self.ui_config.window_width, self.ui_config.window_height)
        self.setMinimumSize(self.ui_config.min_width, self.ui_config.min_height)
        
        # Set window icon from logo
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))
        
        # Set theme
        setTheme(Theme.DARK)
        setThemeColor('#0078D4')  # Windows 11 accent blue
        # Sync window icon with current theme
        self._update_main_logo_assets()
        
        # Create pages
        self._create_pages()
        
        # Setup navigation
        self._setup_navigation()
        
        # Collapse navigation on small screens to save space
        if self.ui_config.nav_collapsed_default:
            self.navigationInterface.setExpandWidth(self.ui_config.nav_width_expanded)
            self.navigationInterface.setCollapsible(True)
        
        # Center window
        self._center_window()
    
    def _create_pages(self):
        """Create all application pages"""
        self.connection_page = ConnectionPage(self)
        self.inventory_page = InventoryPage(self)
        self.settings_page = SettingsPage(self)
        self.gpio_page = GPIOPage(self)
    
    def _setup_navigation(self):
        """Setup the navigation sidebar"""
        # Add pages to navigation
        self.addSubInterface(
            self.connection_page,
            FIF.CONNECT,
            "Connection"
        )
        
        self.addSubInterface(
            self.inventory_page,
            FIF.IOT,
            "Inventory"
        )
        
        self.addSubInterface(
            self.settings_page,
            FIF.SETTING,
            "Reader Settings"
        )
        
        self.addSubInterface(
            self.gpio_page,
            FIF.DEVELOPER_TOOLS,
            "GPIO Control"
        )
        
        # Add separator and bottom items
        self.navigationInterface.addSeparator()
        
        # Theme toggle switch
        from qfluentwidgets import Action
        self.theme_action = Action(FIF.CONSTRACT, 'Toggle Theme')
        self.theme_action.triggered.connect(self._toggle_theme)
        self.navigationInterface.addItem(
            routeKey='theme',
            icon=FIF.CONSTRACT,
            text='Theme',
            onClick=self._toggle_theme,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
        
        # Add logo avatar at bottom if enabled and logo exists
        if self.ui_config.show_logo_in_header and os.path.exists(self.logo_path):
            self.nav_logo_widget = NavigationAvatarWidget('NWS', self.logo_path)
            self.navigationInterface.addWidget(
                routeKey='logo',
                widget=self.nav_logo_widget,
                onClick=self._show_about,
                position=NavigationItemPosition.BOTTOM
            )
        
        # About/Info at bottom
        self.navigationInterface.addItem(
            routeKey='about',
            icon=FIF.INFO,
            text='About',
            onClick=self._show_about,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
    
    def _center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _show_about(self):
        """Show about dialog"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.success(
            title='RFID Reader App',
            content='Modern RFID Tag Reader\nVersion 2.0 - Python Edition\nWindows 11 Fluent Design',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        from qfluentwidgets import isDarkTheme, InfoBar, InfoBarPosition
        
        # Toggle theme
        new_theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
        setTheme(new_theme)
        # Refresh window and navigation logos
        self._update_main_logo_assets()
        # Refresh page logos after theme change
        self._refresh_logos()
        
        # Show notification
        theme_name = "Dark" if new_theme == Theme.DARK else "Light"
        InfoBar.success(
            title='Theme Changed',
            content=f'Switched to {theme_name} mode',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def _current_logo_path(self) -> str:
        """Get the logo path matching the current theme"""
        from qfluentwidgets import isDarkTheme
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = 'logo-nextwaves.png' if isDarkTheme() else 'logo-nextwaves_.png'
        return os.path.join(app_root, filename)

    def _update_main_logo_assets(self):
        """Update window icon and navigation avatar to match theme"""
        self.logo_path = self._current_logo_path()
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))
        if self.nav_logo_widget is not None:
            # Try updating avatar image directly; fallback by recreating if needed
            if hasattr(self.nav_logo_widget, 'setAvatar'):
                self.nav_logo_widget.setAvatar(self.logo_path)
            elif hasattr(self.nav_logo_widget, 'setImage'):
                self.nav_logo_widget.setImage(self.logo_path)
            else:
                # As a fallback, recreate the widget
                self.navigationInterface.removeWidget('logo') if hasattr(self.navigationInterface, 'removeWidget') else None
                self.nav_logo_widget = NavigationAvatarWidget('NWS', self.logo_path)
                self.navigationInterface.addWidget(
                    routeKey='logo',
                    widget=self.nav_logo_widget,
                    onClick=self._show_about,
                    position=NavigationItemPosition.BOTTOM
                )

    def _refresh_logos(self):
        """Refresh logos on all pages to match the current theme"""
        for page in [
            getattr(self, 'connection_page', None),
            getattr(self, 'inventory_page', None),
            getattr(self, 'settings_page', None),
            getattr(self, 'gpio_page', None)
        ]:
            if page and hasattr(page, 'refresh_logo'):
                page.refresh_logo()
    
    # ============================================================
    # Public interface methods for controller
    # ============================================================
    
    def set_connected_state(self, connected: bool, message: str = ""):
        """Update UI for connection state"""
        self.connection_page.set_connected(connected, message)
        self.inventory_page.set_enabled(connected)
        self.settings_page.set_enabled(connected)
        self.gpio_page.set_enabled(connected)
    
    def append_log(self, message: str, log_type: int = 0):
        """Append message to log"""
        self.connection_page.append_log(message, log_type)
    
    def update_tag_list(self, tags: list):
        """Update the inventory tag list"""
        self.inventory_page.update_tag_list(tags)
    
    def update_detected_tags(self, tags: list):
        """Update the detected tags list"""
        self.inventory_page.update_detected_tags(tags)
    
    def update_tag_counts(self, unique_count: int, total_count: int):
        """Update tag count displays"""
        self.inventory_page.update_counts(unique_count, total_count)
    
    def set_inventory_running(self, running: bool):
        """Update UI for inventory running state"""
        self.inventory_page.set_running(running)
    
    def update_reader_info(self, info: dict):
        """Update reader information display"""
        self.settings_page.update_reader_info(info)
    
    def update_gpio_state(self, gpio_states: dict):
        """Update GPIO state display"""
        self.gpio_page.update_gpio_state(gpio_states)
    
    def get_available_ports(self) -> list:
        """Get list of available serial ports"""
        from utils import get_available_ports
        return get_available_ports()
    
    def refresh_ports(self):
        """Refresh available ports in connection page"""
        self.connection_page.refresh_ports()

