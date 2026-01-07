"""
Inventory Page - Real-time RFID Tag Inventory
Windows 11 Fluent Design
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    PrimaryPushButton, PushButton, ToggleButton,
    CheckBox, RadioButton, ComboBox, SpinBox,
    IconWidget, InfoBar, InfoBarPosition, TableWidget,
    FluentIcon as FIF, ProgressRing, TransparentPushButton
)

# Import responsive UI configuration
from utils.ui_config import get_ui_config


class StatsCard(CardWidget):
    """Statistics display card - Compact inline version"""
    
    def __init__(self, title: str, icon: FIF, parent=None):
        super().__init__(parent)
        self.ui_config = get_ui_config()
        self._setup_ui(title, icon)
    
    def _setup_ui(self, title: str, icon: FIF):
        layout = QHBoxLayout(self)
        margin = self.ui_config.card_margin - 4  # Slightly less for cards
        layout.setContentsMargins(margin, margin // 2, margin, margin // 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Icon
        icon_widget = IconWidget(icon, self)
        icon_size = self.ui_config.icon_small
        icon_widget.setFixedSize(icon_size, icon_size)
        layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Text content - vertical stack
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = CaptionLabel(title, self)
        title_label.setStyleSheet(f"color: #888; font-size: {self.ui_config.font_caption}px;")
        text_layout.addWidget(title_label)
        
        self.value_label = StrongBodyLabel("0", self)
        self.value_label.setFont(QFont("Segoe UI", self.ui_config.font_stats_value, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #0078D4;")
        text_layout.addWidget(self.value_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
    
    def set_value(self, value):
        """Set the displayed value"""
        self.value_label.setText(str(value))


class AntennaControlCard(CardWidget):
    """Antenna selection control card - Toolbar style single row"""
    
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_config = get_ui_config()
        self._setup_ui()
        self.setFixedHeight(self.ui_config.toolbar_height)
    
    def _setup_ui(self):
        # Single horizontal row layout
        layout = QHBoxLayout(self)
        # Ultra compact margins on small screens
        margin = 6 if self.ui_config.profile == 'small' else self.ui_config.card_margin
        layout.setContentsMargins(margin, 0, margin, 0)
        layout.setSpacing(3 if self.ui_config.profile == 'small' else 6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Title label (hide on small screens to save space)
        if self.ui_config.profile != 'small':
            title = StrongBodyLabel("Antenna", self)
            title.setStyleSheet("color: #333;")
            title.setFont(QFont("Segoe UI", self.ui_config.font_body, QFont.Weight.DemiBold))
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter)
            
            # Visual separator
            layout.addSpacing(8)
            self._add_separator(layout)
            layout.addSpacing(8)
        else:
            # On small screens, add compact label
            title = CaptionLabel("Ant:", self)
            title.setStyleSheet("color: #666; font-weight: bold;")
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(2)
        
        # Antenna checkboxes
        self.ant_checks = []
        for i in range(4):
            cb = CheckBox(f"{i + 1}", self)
            cb.setChecked(i < 2)  # Enable first two by default
            cb.stateChanged.connect(self._on_config_changed)
            self.ant_checks.append(cb)
            layout.addWidget(cb, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Visual separator (compact on small screens)
        spacing = 4 if self.ui_config.profile == 'small' else 12
        layout.addSpacing(spacing)
        if self.ui_config.profile != 'small':
            self._add_separator(layout)
            layout.addSpacing(spacing)
        
        # Session selection
        session_label = CaptionLabel("Ses:" if self.ui_config.profile == 'small' else "Session", self)
        session_label.setStyleSheet("color: #666; font-weight: bold;" if self.ui_config.profile == 'small' else "color: #666;")
        layout.addWidget(session_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(2 if self.ui_config.profile == 'small' else 4)
        
        self.session_group = []
        for name in ['S0', 'S1', 'S2', 'S3']:
            rb = RadioButton(name, self)
            rb.clicked.connect(self._on_config_changed)
            self.session_group.append(rb)
            layout.addWidget(rb, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.session_group[0].setChecked(True)
        
        # Visual separator (compact on small screens)
        spacing = 4 if self.ui_config.profile == 'small' else 12
        layout.addSpacing(spacing)
        if self.ui_config.profile != 'small':
            self._add_separator(layout)
            layout.addSpacing(spacing)
        
        # Target selection
        target_label = CaptionLabel("Tgt:" if self.ui_config.profile == 'small' else "Target", self)
        target_label.setStyleSheet("color: #666; font-weight: bold;" if self.ui_config.profile == 'small' else "color: #666;")
        layout.addWidget(target_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(2 if self.ui_config.profile == 'small' else 4)
        
        self.target_a = RadioButton("A", self)
        self.target_b = RadioButton("B", self)
        self.target_a.setChecked(True)
        self.target_a.clicked.connect(self._on_config_changed)
        self.target_b.clicked.connect(self._on_config_changed)
        
        layout.addWidget(self.target_a, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.target_b, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
    
    def _add_separator(self, layout):
        """Add a vertical separator line"""
        from PyQt6.QtWidgets import QFrame
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E0E0E0;")
        sep.setFixedHeight(28)
        layout.addWidget(sep, alignment=Qt.AlignmentFlag.AlignVCenter)
    
    def _on_config_changed(self):
        """Emit configuration when changed"""
        config = self.get_config()
        self.config_changed.emit(config)
    
    def get_config(self) -> dict:
        """Get current antenna configuration"""
        session = 0
        for i, rb in enumerate(self.session_group):
            if rb.isChecked():
                session = i
                break
        
        return {
            'antennas': [cb.isChecked() for cb in self.ant_checks],
            'session': session,
            'target': 'A' if self.target_a.isChecked() else 'B'
        }


class TagTableWidget(TableWidget):
    """Custom styled table for tag display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
    
    def _setup_style(self):
        """Setup table styling"""
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        
        # Style
        self.setStyleSheet("""
            TagTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            TagTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            TagTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            TagTableWidget::item:hover {
                background-color: #F5F5F5;
            }
            QHeaderView::section {
                background-color: #F8F8F8;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #0078D4;
                font-weight: bold;
                color: #333;
            }
        """)


class InventoryPage(QWidget):
    """Main inventory operation page"""
    
    start_inventory = pyqtSignal(dict)
    stop_inventory = pyqtSignal()
    clear_data = pyqtSignal()
    export_data = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inventoryPage")
        self._is_running = False
        self.ui_config = get_ui_config()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(self.ui_config.layout_spacing)
        layout.setContentsMargins(
            self.ui_config.page_margin_h,
            self.ui_config.page_margin_v,
            self.ui_config.page_margin_h,
            self.ui_config.page_margin_v
        )
        
        # ============================================================
        # ROW 1: Page title (minimal space)
        # ============================================================
        title = StrongBodyLabel("Real-Time Inventory", self)
        title.setFont(QFont("Segoe UI", self.ui_config.font_page_title, QFont.Weight.DemiBold))
        layout.addWidget(title)
        
        # ============================================================
        # ROW 2: Stats cards (fixed height, no stretch)
        # ============================================================
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(self.ui_config.card_spacing)
        
        self.unique_tags_card = StatsCard("Unique Tags", FIF.TAG, self)
        self.total_reads_card = StatsCard("Total Reads", FIF.CALORIES, self)
        self.detected_card = StatsCard("Detected (Coming)", FIF.CHECKBOX, self)
        
        # Set fixed height for stats cards - they will expand equally to fill width
        card_height = self.ui_config.stats_card_height
        for card in [self.unique_tags_card, self.total_reads_card, self.detected_card]:
            card.setFixedHeight(card_height)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        stats_layout.addWidget(self.unique_tags_card, 1)
        stats_layout.addWidget(self.total_reads_card, 1)
        stats_layout.addWidget(self.detected_card, 1)
        
        layout.addLayout(stats_layout, 3)  # Stretch factor 0 - fixed
        
        # ============================================================
        # ROW 3: TOOLBAR - Single row controls + actions
        # ============================================================
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(self.ui_config.card_spacing)
        
        # Action buttons card - stretch factor 1 (positioned first now)
        btn_frame = CardWidget(self)
        btn_frame.setFixedHeight(self.ui_config.toolbar_height)
        # Much smaller minimum width for small screens
        btn_frame.setMinimumWidth(200 if self.ui_config.profile == 'small' else 420)
        btn_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_layout = QHBoxLayout(btn_frame)
        btn_margin = 6 if self.ui_config.profile == 'small' else self.ui_config.card_margin
        btn_layout.setContentsMargins(btn_margin, 0, btn_margin, 0)
        btn_layout.setSpacing(3 if self.ui_config.profile == 'small' else self.ui_config.layout_spacing)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Action label (hide on small screens to save space)
        if self.ui_config.profile != 'small':
            btn_title = CaptionLabel("Actions", self)
            btn_title.setStyleSheet("color: #666;")
            btn_layout.addWidget(btn_title, alignment=Qt.AlignmentFlag.AlignVCenter)
            btn_layout.addSpacing(8)
        
        # Toolbar buttons - Compact on small screens to save space
        if self.ui_config.profile == 'small':
            # Very short text buttons for compact layout
            self.start_btn = PrimaryPushButton(FIF.PLAY, "Start", self)
            self.start_btn.setToolTip("Start Inventory")
            self.stop_btn = PushButton(FIF.PAUSE, "Stop", self)
            self.stop_btn.setToolTip("Stop Inventory")
            self.stop_btn.setEnabled(False)
            self.clear_btn = PushButton(FIF.DELETE, "Del", self)
            self.clear_btn.setToolTip("Clear Data")
            self.export_btn = PushButton(FIF.SAVE, "Exp", self)
            self.export_btn.setToolTip("Export to Excel")
            
            # Compact square buttons
            btn_width = self.ui_config.button_height * 3 - 20
            self.start_btn.setFixedWidth(btn_width)
            self.stop_btn.setFixedWidth(btn_width)
            self.clear_btn.setFixedWidth(btn_width)
            self.export_btn.setFixedWidth(btn_width)
        else:
            # Full buttons with text on larger screens
            self.start_btn = PrimaryPushButton(FIF.PLAY, "Start", self)
            self.stop_btn = PushButton(FIF.PAUSE, "Stop", self)
            self.stop_btn.setEnabled(False)
            self.clear_btn = PushButton(FIF.DELETE, "Clear", self)
            self.export_btn = PushButton(FIF.SAVE, "Export", self)
            
            btn_width = 90
            self.start_btn.setMinimumWidth(btn_width)
            self.stop_btn.setMinimumWidth(btn_width - 5)
            self.clear_btn.setMinimumWidth(btn_width - 5)
            self.export_btn.setMinimumWidth(btn_width)
        
        # Uniform button styling
        btn_height = self.ui_config.button_height
        for btn in [self.start_btn, self.stop_btn, self.clear_btn, self.export_btn]:
            btn.setFixedHeight(btn_height)
            # Policy: Minimum = can expand but won't shrink below minimum
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        btn_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        btn_layout.addWidget(self.stop_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        btn_layout.addWidget(self.clear_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        btn_layout.addWidget(self.export_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Add Actions panel with stretch factor 1
        toolbar_layout.addWidget(btn_frame, 2)
        
        # Antenna control card (toolbar style) - stretch factor 2 (positioned after actions now)
        self.antenna_card = AntennaControlCard(self)
        toolbar_layout.addWidget(self.antenna_card, 3)
        
        layout.addLayout(toolbar_layout, 0)  # Stretch factor 0 - toolbar is fixed height
        
        # ============================================================
        # ROW 4: Data Tables - EXPAND to fill remaining space
        # ============================================================
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(self.ui_config.card_spacing)
        
        # Inventory list
        inv_frame = CardWidget(self)
        inv_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inv_layout = QVBoxLayout(inv_frame)
        card_margin = self.ui_config.card_margin
        inv_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        inv_layout.setSpacing(6)
        
        inv_title = StrongBodyLabel("Inventory List", self)
        inv_title.setFont(QFont("Segoe UI", self.ui_config.font_card_title, QFont.Weight.DemiBold))
        inv_layout.addWidget(inv_title)
        
        self.inventory_table = TagTableWidget(self)
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["EPC", "Antenna", "Count", "RSSI", "Frequency"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            self.inventory_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.inventory_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        inv_layout.addWidget(self.inventory_table, 1)
        tables_layout.addWidget(inv_frame, 1)  
        
        # Detected tags list
        det_frame = CardWidget(self)
        det_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        det_layout = QVBoxLayout(det_frame)
        det_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        det_layout.setSpacing(6)
        
        det_title = StrongBodyLabel("Detected Tags (Coming)", self)
        det_title.setFont(QFont("Segoe UI", self.ui_config.font_card_title, QFont.Weight.DemiBold))
        det_layout.addWidget(det_title)
        
        self.detected_table = TagTableWidget(self)
        self.detected_table.setColumnCount(5)
        self.detected_table.setHorizontalHeaderLabels(["EPC", "REL1", "REL2", "REL&", "DIR"])
        self.detected_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            self.detected_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.detected_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        det_layout.addWidget(self.detected_table, 1)
        tables_layout.addWidget(det_frame, 1)  
        
        layout.addLayout(tables_layout, 6)  # Stretch factor 6 - larger tables section
        
        # Connect signals
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.clear_btn.clicked.connect(self._on_clear)
        self.export_btn.clicked.connect(self.export_data.emit)
    
    def _on_start(self):
        """Handle start button click"""
        config = self.antenna_card.get_config()
        self.start_inventory.emit(config)
    
    def _on_stop(self):
        """Handle stop button click"""
        self.stop_inventory.emit()
    
    def _on_clear(self):
        """Handle clear button click"""
        self.inventory_table.setRowCount(0)
        self.detected_table.setRowCount(0)
        self.unique_tags_card.set_value(0)
        self.total_reads_card.set_value(0)
        self.detected_card.set_value(0)
        self.clear_data.emit()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable the page controls"""
        self.start_btn.setEnabled(enabled and not self._is_running)
        self.antenna_card.setEnabled(enabled)
    
    def set_running(self, running: bool):
        """Update running state"""
        self._is_running = running
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.antenna_card.setEnabled(not running)
        
        if running:
            self.start_btn.setText("Running")
        else:
            self.start_btn.setText("Start")
    
    def update_counts(self, unique: int, total: int):
        """Update tag count displays"""
        self.unique_tags_card.set_value(unique)
        self.total_reads_card.set_value(total)
    
    def update_tag_list(self, tags: list):
        """
        Update inventory table with tags
        tags: list of dicts with keys: epc, antenna, count, rssi, frequency
        """
        self.inventory_table.setRowCount(len(tags))
        
        for row, tag in enumerate(tags):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(tag.get('epc', '')))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(str(tag.get('antenna', ''))))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(str(tag.get('count', ''))))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rssi', ''))))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(tag.get('frequency', ''))))
            
            # Center align numeric columns
            for col in [1, 2, 3]:
                item = self.inventory_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def add_tag(self, tag: dict):
        """Add or update a single tag in the table"""
        epc = tag.get('epc', '')
        
        # Find existing row
        for row in range(self.inventory_table.rowCount()):
            item = self.inventory_table.item(row, 0)
            if item and item.text() == epc:
                # Update existing row
                self.inventory_table.setItem(row, 1, QTableWidgetItem(str(tag.get('antenna', ''))))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(str(tag.get('count', ''))))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rssi', ''))))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(str(tag.get('frequency', ''))))
                return
        
        # Add new row
        row = self.inventory_table.rowCount()
        self.inventory_table.insertRow(row)
        self.inventory_table.setItem(row, 0, QTableWidgetItem(epc))
        self.inventory_table.setItem(row, 1, QTableWidgetItem(str(tag.get('antenna', ''))))
        self.inventory_table.setItem(row, 2, QTableWidgetItem(str(tag.get('count', ''))))
        self.inventory_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rssi', ''))))
        self.inventory_table.setItem(row, 4, QTableWidgetItem(str(tag.get('frequency', ''))))
    
    def add_tags_batch(self, tags: list):
        """
        Add or update multiple tags in a single batch operation
        
        RASPBERRY PI OPTIMIZATION:
        - Disables table updates during batch processing
        - Builds an index of existing EPCs for O(1) lookup
        - Processes all tags before re-enabling updates
        - Significantly reduces GPU/CPU load on Pi
        """
        if not tags:
            return
        
        # Disable updates during batch operation for better performance
        self.inventory_table.setUpdatesEnabled(False)
        
        try:
            # Build index of existing EPCs -> row numbers for fast lookup
            # This converts O(n*m) to O(n+m) where n=tags, m=rows
            epc_to_row = {}
            for row in range(self.inventory_table.rowCount()):
                item = self.inventory_table.item(row, 0)
                if item:
                    epc_to_row[item.text()] = row
            
            # Process all tags
            for tag in tags:
                epc = tag.get('epc', '')
                if not epc:
                    continue
                
                if epc in epc_to_row:
                    # Update existing row
                    row = epc_to_row[epc]
                    self.inventory_table.setItem(row, 1, QTableWidgetItem(str(tag.get('antenna', ''))))
                    self.inventory_table.setItem(row, 2, QTableWidgetItem(str(tag.get('count', ''))))
                    self.inventory_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rssi', ''))))
                    self.inventory_table.setItem(row, 4, QTableWidgetItem(str(tag.get('frequency', ''))))
                else:
                    # Add new row
                    row = self.inventory_table.rowCount()
                    self.inventory_table.insertRow(row)
                    self.inventory_table.setItem(row, 0, QTableWidgetItem(epc))
                    self.inventory_table.setItem(row, 1, QTableWidgetItem(str(tag.get('antenna', ''))))
                    self.inventory_table.setItem(row, 2, QTableWidgetItem(str(tag.get('count', ''))))
                    self.inventory_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rssi', ''))))
                    self.inventory_table.setItem(row, 4, QTableWidgetItem(str(tag.get('frequency', ''))))
                    # Update index
                    epc_to_row[epc] = row
        
        finally:
            # Re-enable updates and trigger a single repaint
            self.inventory_table.setUpdatesEnabled(True)
    
    def update_detected_tags(self, tags: list):
        """
        Update detected tags table
        tags: list of AnalysisResult objects or dicts
        """
        self.detected_table.setRowCount(len(tags))
        self.detected_card.set_value(len(tags))
        
        for row, tag in enumerate(tags):
            if hasattr(tag, 'epc'):  # AnalysisResult object
                self.detected_table.setItem(row, 0, QTableWidgetItem(tag.epc))
                self.detected_table.setItem(row, 1, QTableWidgetItem(f"{tag.confidence_ant1:.1f}"))
                self.detected_table.setItem(row, 2, QTableWidgetItem(f"{tag.confidence_ant2:.1f}"))
                self.detected_table.setItem(row, 3, QTableWidgetItem(f"{tag.confidence_all:.1f}"))
                self.detected_table.setItem(row, 4, QTableWidgetItem(tag.direction.name))
            else:  # dict
                self.detected_table.setItem(row, 0, QTableWidgetItem(tag.get('epc', '')))
                self.detected_table.setItem(row, 1, QTableWidgetItem(str(tag.get('rel1', ''))))
                self.detected_table.setItem(row, 2, QTableWidgetItem(str(tag.get('rel2', ''))))
                self.detected_table.setItem(row, 3, QTableWidgetItem(str(tag.get('rel_all', ''))))
                self.detected_table.setItem(row, 4, QTableWidgetItem(str(tag.get('direction', ''))))
            
            # Center align
            for col in range(1, 5):
                item = self.detected_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

