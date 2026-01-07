"""
Custom HUD Widgets - Cyberpunk/Sci-Fi Components
Angular borders, glowing effects, and futuristic data cards

This module provides custom PyQt6 widgets designed for a
military/industrial robotics control panel aesthetic:

- HUDCard: Container with chamfered corners and optional glow
- HUDStatsWidget: Data display widget with large numeric value
- TagGridView: Grid layout for tag cards
- TagCardWidget: Individual tag data card with signal visualization
- HUDButton: Custom button with angular styling and hover glow
"""

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QFont, QIcon

from qfluentwidgets import FluentIcon as FIF, IconWidget

from .theme import HUDColors, HUDFonts


class HUDCard(QFrame):
    """
    Container widget with angular/chamfered corners
    Optional glowing border effect
    
    This is the base container for HUD panels and cards.
    Features:
    - Angular borders (no rounded corners)
    - Optional chamfered/cut corners
    - Configurable border color
    - Optional glow effect
    """
    
    def __init__(self, parent=None, corner_size: int = 10, glow: bool = False, 
                 border_color: str = None):
        super().__init__(parent)
        self.corner_size = corner_size
        self.glow_enabled = glow
        self.border_color = border_color or HUDColors.BORDER
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup card styling"""
        # Use QSS for basic styling
        glow_shadow = ""
        if self.glow_enabled:
            glow_shadow = f"""
                QFrame {{
                    border: 2px solid {self.border_color};
                    background-color: {HUDColors.BG_CARD};
                }}
            """
        else:
            glow_shadow = f"""
                QFrame {{
                    border: 1px solid {self.border_color};
                    background-color: {HUDColors.BG_CARD};
                }}
            """
        
        self.setStyleSheet(glow_shadow)
        self.setFrameShape(QFrame.Shape.StyledPanel)
    
    def paintEvent(self, event):
        """Custom paint for chamfered corners if needed"""
        super().paintEvent(event)
        
        # For chamfered corners, we would use QPainter to draw custom shapes
        # For now, keeping it simple with standard angular borders
        # Advanced chamfering can be added if needed


class HUDStatsWidget(QWidget):
    """
    HUD statistics display widget
    Shows an icon, label, and large numeric value
    
    Example:
        widget = HUDStatsWidget("Unique Tags", FIF.TAG)
        widget.set_value(42)
    """
    
    def __init__(self, label: str, icon: FIF, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.icon = icon
        self._value = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup widget layout"""
        # Container frame with HUD styling
        container = HUDCard(self, corner_size=0, border_color=HUDColors.BORDER)
        container.setFixedHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        
        # Inner layout
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(15, 10, 15, 10)
        inner_layout.setSpacing(5)
        
        # Top row: Icon + Label
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        icon_widget = IconWidget(self.icon, self)
        icon_widget.setFixedSize(20, 20)
        
        label = QLabel(self.label_text.upper(), self)
        label.setFont(HUDFonts.get_display_font(9, bold=True))
        label.setStyleSheet(f"color: {HUDColors.TEXT_DIM}; letter-spacing: 1px;")
        
        top_row.addWidget(icon_widget)
        top_row.addWidget(label)
        top_row.addStretch()
        
        inner_layout.addLayout(top_row)
        
        # Value display
        self.value_label = QLabel("0", self)
        self.value_label.setFont(HUDFonts.get_monospace_font(28, bold=True))
        self.value_label.setStyleSheet(f"color: {HUDColors.PRIMARY};")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        inner_layout.addWidget(self.value_label)
        inner_layout.addStretch()
        
        # Left accent border
        self.setStyleSheet(f"""
            QWidget {{
                border-left: 4px solid {HUDColors.PRIMARY_DIM};
            }}
        """)
    
    def set_value(self, value: int):
        """Update the displayed value"""
        self._value = value
        self.value_label.setText(str(value))


class TagCardWidget(QFrame):
    """
    Individual tag data card for grid view
    Displays tag information with visual signal indicator
    
    Features:
    - Glowing border effect
    - Signal strength visualization (fake bars/graph)
    - Monospaced data display
    - Compact layout optimized for grid
    """
    
    def __init__(self, tag_data: dict, parent=None):
        super().__init__(parent)
        self.tag_data = tag_data
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup tag card UI"""
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Glowing border styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {HUDColors.BG_PANEL};
                border: 2px solid {HUDColors.PRIMARY};
                padding: 8px;
            }}
            QFrame:hover {{
                border-color: {HUDColors.PRIMARY};
                background-color: {HUDColors.BG_CARD};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # EPC (truncated if too long)
        epc = self.tag_data.get('epc', 'UNKNOWN')
        if len(epc) > 20:
            epc_display = epc[:18] + "..."
        else:
            epc_display = epc
        
        epc_label = QLabel(f"EPC: {epc_display}", self)
        epc_label.setFont(HUDFonts.get_monospace_font(9, bold=True))
        epc_label.setStyleSheet(f"color: {HUDColors.PRIMARY}; background: transparent; border: none;")
        layout.addWidget(epc_label)
        
        # Separator line
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {HUDColors.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(line)
        
        # Data grid
        data_grid = QGridLayout()
        data_grid.setSpacing(4)
        data_grid.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Antenna / RSSI
        ant_label = QLabel("ANT:", self)
        ant_label.setFont(HUDFonts.get_display_font(8))
        ant_label.setStyleSheet(f"color: {HUDColors.TEXT_DIM}; background: transparent; border: none;")
        
        ant_value = QLabel(str(self.tag_data.get('antenna', '-')), self)
        ant_value.setFont(HUDFonts.get_monospace_font(9, bold=True))
        ant_value.setStyleSheet(f"color: {HUDColors.TEXT_PRIMARY}; background: transparent; border: none;")
        
        rssi_label = QLabel("RSSI:", self)
        rssi_label.setFont(HUDFonts.get_display_font(8))
        rssi_label.setStyleSheet(f"color: {HUDColors.TEXT_DIM}; background: transparent; border: none;")
        
        rssi_value = QLabel(str(self.tag_data.get('rssi', '-')), self)
        rssi_value.setFont(HUDFonts.get_monospace_font(9, bold=True))
        rssi_value.setStyleSheet(f"color: {HUDColors.SUCCESS}; background: transparent; border: none;")
        
        data_grid.addWidget(ant_label, 0, 0)
        data_grid.addWidget(ant_value, 0, 1)
        data_grid.addWidget(rssi_label, 0, 2)
        data_grid.addWidget(rssi_value, 0, 3)
        
        # Row 2: Count / Direction
        cnt_label = QLabel("CNT:", self)
        cnt_label.setFont(HUDFonts.get_display_font(8))
        cnt_label.setStyleSheet(f"color: {HUDColors.TEXT_DIM}; background: transparent; border: none;")
        
        cnt_value = QLabel(str(self.tag_data.get('count', '-')), self)
        cnt_value.setFont(HUDFonts.get_monospace_font(9, bold=True))
        cnt_value.setStyleSheet(f"color: {HUDColors.TEXT_PRIMARY}; background: transparent; border: none;")
        
        dir_label = QLabel("DIR:", self)
        dir_label.setFont(HUDFonts.get_display_font(8))
        dir_label.setStyleSheet(f"color: {HUDColors.TEXT_DIM}; background: transparent; border: none;")
        
        dir_value = QLabel(str(self.tag_data.get('rssi', '-')), self)  # Using rssi field for direction
        dir_value.setFont(HUDFonts.get_monospace_font(9, bold=True))
        dir_value.setStyleSheet(f"color: {HUDColors.SECONDARY}; background: transparent; border: none;")
        
        data_grid.addWidget(cnt_label, 1, 0)
        data_grid.addWidget(cnt_value, 1, 1)
        data_grid.addWidget(dir_label, 1, 2)
        data_grid.addWidget(dir_value, 1, 3)
        
        layout.addLayout(data_grid)
        
        # Signal strength visualization (simple bars)
        signal_container = QHBoxLayout()
        signal_container.setSpacing(2)
        signal_container.setContentsMargins(0, 4, 0, 0)
        
        # Create fake signal bars (3 bars for visual effect)
        for i in range(8):
            bar = QFrame(self)
            bar.setFixedWidth(8)
            bar.setFixedHeight(4 + i * 2)
            if i < 5:  # First 5 bars are "active"
                bar.setStyleSheet(f"background-color: {HUDColors.PRIMARY}; border: none;")
            else:
                bar.setStyleSheet(f"background-color: {HUDColors.BORDER_DIM}; border: none;")
            signal_container.addWidget(bar, alignment=Qt.AlignmentFlag.AlignBottom)
        
        signal_container.addStretch()
        layout.addLayout(signal_container)


class TagGridView(QWidget):
    """
    Grid view container for tag cards
    Automatically arranges TagCardWidgets in a responsive grid
    
    Features:
    - Scrollable container
    - Configurable column count
    - Auto-layout management
    """
    
    def __init__(self, parent=None, columns: int = 3):
        super().__init__(parent)
        self.columns = columns
        self.tag_widgets = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup scrollable grid container"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Container widget for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
    
    def add_tag(self, tag_data: dict):
        """Add a tag card to the grid"""
        card = TagCardWidget(tag_data, self)
        self.tag_widgets.append(card)
        
        # Calculate grid position
        index = len(self.tag_widgets) - 1
        row = index // self.columns
        col = index % self.columns
        
        self.grid_layout.addWidget(card, row, col)
    
    def clear_tags(self):
        """Remove all tag cards"""
        for widget in self.tag_widgets:
            widget.deleteLater()
        self.tag_widgets.clear()
    
    def set_columns(self, columns: int):
        """Update grid column count and re-layout"""
        self.columns = columns
        self._relayout()
    
    def _relayout(self):
        """Re-arrange widgets in grid"""
        for i, widget in enumerate(self.tag_widgets):
            row = i // self.columns
            col = i % self.columns
            self.grid_layout.addWidget(widget, row, col)


class HUDButton(QPushButton):
    """
    Custom HUD-styled button with glow effect
    
    Features:
    - Angular borders
    - Hover glow animation
    - Monospaced text
    - Icon support
    """
    
    def __init__(self, text: str = "", icon: FIF = None, parent=None):
        super().__init__(text, parent)
        self._setup_ui(icon)
    
    def _setup_ui(self, icon):
        """Setup button styling"""
        if icon:
            self.setIcon(icon.icon())
        
        self.setFont(HUDFonts.get_display_font(10, bold=True))
        
        # Override global style for enhanced glow effect
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {HUDColors.BG_PANEL};
                color: {HUDColors.PRIMARY};
                border: 2px solid {HUDColors.PRIMARY_DIM};
                padding: 10px 20px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: {HUDColors.PRIMARY_DARK};
                border-color: {HUDColors.PRIMARY};
                color: {HUDColors.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {HUDColors.PRIMARY_DIM};
                color: {HUDColors.BG_DARK};
            }}
            QPushButton:disabled {{
                background-color: {HUDColors.BG_DARKER};
                border-color: {HUDColors.BORDER_DIM};
                color: {HUDColors.TEXT_DISABLED};
            }}
        """)


class HUDSeparator(QFrame):
    """
    Visual separator line for HUD panels
    """
    
    def __init__(self, vertical: bool = False, parent=None):
        super().__init__(parent)
        if vertical:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(2)
        else:
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(2)
        
        self.setStyleSheet(f"background-color: {HUDColors.BORDER};")


class HUDPanel(HUDCard):
    """
    Main content panel with title bar
    
    Example:
        panel = HUDPanel("SYSTEM STATUS", parent)
        panel.add_widget(my_content_widget)
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent, corner_size=0, border_color=HUDColors.BORDER)
        self.title = title
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup panel with title bar"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = QFrame(self)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {HUDColors.BG_DARKER};
                border-bottom: 2px solid {HUDColors.PRIMARY};
                padding: 10px 15px;
            }}
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(f"◢ {self.title} ◣", self)
        title_label.setFont(HUDFonts.get_display_font(12, bold=True))
        title_label.setStyleSheet(f"color: {HUDColors.PRIMARY}; letter-spacing: 2px; background: transparent; border: none;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addWidget(title_bar)
        
        # Content container
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        
        layout.addWidget(self.content_widget)
    
    def add_widget(self, widget: QWidget):
        """Add widget to panel content area"""
        self.content_layout.addWidget(widget)
