"""
Settings Page - Reader Configuration
Clean, Touch-Friendly UI for RFID Reader Settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QSpacerItem, QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    PrimaryPushButton, PushButton, ComboBox, RadioButton,
    SpinBox, IconWidget, SwitchButton, FluentIcon as FIF,
    SmoothScrollArea
)


# ============================================================
# INFO CARD - Reader Information Display
# ============================================================
class InfoCard(CardWidget):
    """
    Displays reader information (Firmware, ID, Temperature).
    
    Layout: QGridLayout with 4 columns
    - Col 0: Icon (fixed 24px)
    - Col 1: Label name (STRETCHES to fill space)
    - Col 2: Value display (min 100px)
    - Col 3: Refresh button (fixed 100px)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # ─── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)
        
        icon = IconWidget(FIF.INFO, self)
        icon.setFixedSize(24, 24)
        header.addWidget(icon)
        
        title = StrongBodyLabel("Reader Information", self)
        header.addWidget(title)
        header.addStretch()
        
        main_layout.addLayout(header)
        
        # ─── Info Grid ────────────────────────────────────────
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(16)
        
        # CRITICAL: Column stretch factors
        grid.setColumnStretch(0, 0)  # Icon - fixed
        grid.setColumnStretch(1, 1)  # Label - STRETCHES (prevents clipping)
        grid.setColumnStretch(2, 0)  # Value - min width
        grid.setColumnStretch(3, 0)  # Button - fixed
        
        # Define info rows
        info_items = [
            (FIF.CODE, "Firmware Version", "firmware", "#0078D4"),
            (FIF.FINGERPRINT, "Reader ID", "reader_id", "#6366F1"),
            (FIF.CALORIES, "Temperature", "temperature", "#EF4444"),
        ]
        
        self.value_labels = {}
        
        for row, (icon_type, label_text, key, color) in enumerate(info_items):
            # Column 0: Icon
            row_icon = IconWidget(icon_type, self)
            row_icon.setFixedSize(20, 20)
            grid.addWidget(row_icon, row, 0, Qt.AlignmentFlag.AlignVCenter)
            
            # Column 1: Label (stretches to prevent clipping)
            label = BodyLabel(label_text, self)
            label.setMinimumHeight(40)  # Touch-friendly row height
            grid.addWidget(label, row, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            
            # Column 2: Value display
            value = BodyLabel("--", self)
            value.setStyleSheet(f"color: {color}; font-weight: bold;")
            value.setMinimumWidth(100)
            self.value_labels[key] = value
            grid.addWidget(value, row, 2, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            
            # Column 3: Refresh button (fixed width)
            btn = PushButton("Refresh", self, FIF.SYNC)
            btn.setFixedWidth(100)
            btn.setFixedHeight(38)
            setattr(self, f"get_{key}_btn", btn)
            grid.addWidget(btn, row, 3, Qt.AlignmentFlag.AlignVCenter)
        
        main_layout.addLayout(grid)
        main_layout.addStretch()
    
    def update_info(self, info: dict):
        """Update displayed values from reader response"""
        if 'firmware' in info:
            self.value_labels['firmware'].setText(str(info['firmware']))
        if 'reader_id' in info:
            self.value_labels['reader_id'].setText(str(info['reader_id']))
        if 'temperature' in info:
            self.value_labels['temperature'].setText(str(info['temperature']))


# ============================================================
# POWER CARD - Antenna Power Configuration
# ============================================================
class PowerCard(CardWidget):
    """
    Configure reader power settings.
    
    Sections:
    1. Global Power: Set all antennas to same power
    2. Per-Antenna: 2x2 grid for individual antenna power
    
    FIX: "Apply" button uses addStretch() to prevent full-width stretching
    FIX: SpinBox text forced to black (not green)
    """
    
    set_power = pyqtSignal(int)
    set_power_per_antenna = pyqtSignal(int, int, int, int)
    get_power = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # ─── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)
        
        icon = IconWidget(FIF.SPEED_HIGH, self)
        icon.setFixedSize(24, 24)
        header.addWidget(icon)
        
        title = StrongBodyLabel("Power Settings", self)
        header.addWidget(title)
        header.addStretch()
        
        self.get_power_btn = PushButton("Read Current", self, FIF.SYNC)
        self.get_power_btn.setFixedHeight(38)
        header.addWidget(self.get_power_btn)
        
        main_layout.addLayout(header)
        
        # ─── Section 1: Global Power ──────────────────────────
        global_label = BodyLabel("Global Power (All Antennas)", self)
        global_label.setStyleSheet("font-weight: 600;")
        main_layout.addWidget(global_label)
        
        global_row = QHBoxLayout()
        global_row.setSpacing(12)
        
        self.power_combo = ComboBox(self)
        self.power_combo.addItems([f"{i} dBm" for i in range(0, 34)])
        self.power_combo.setCurrentIndex(30)
        self.power_combo.setFixedHeight(40)
        self.power_combo.setMinimumWidth(120)
        global_row.addWidget(self.power_combo)
        
        self.set_all_btn = PrimaryPushButton("Set All", self, FIF.ACCEPT)
        self.set_all_btn.setFixedHeight(40)
        self.set_all_btn.setFixedWidth(100)
        global_row.addWidget(self.set_all_btn)
        
        global_row.addStretch()
        main_layout.addLayout(global_row)
        
        # ─── Separator ────────────────────────────────────────
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # ─── Section 2: Per-Antenna Power (2x2 Grid) ──────────
        per_ant_label = BodyLabel("Per-Antenna Power", self)
        per_ant_label.setStyleSheet("font-weight: 600;")
        main_layout.addWidget(per_ant_label)
        
        # 2x2 Grid layout
        ant_grid = QGridLayout()
        ant_grid.setSpacing(16)
        ant_grid.setColumnStretch(0, 1)
        ant_grid.setColumnStretch(1, 1)
        
        self.ant_spinboxes = []
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
        
        for i in range(4):
            row = i // 2
            col = i % 2
            
            # Horizontal layout for each antenna
            ant_layout = QHBoxLayout()
            ant_layout.setSpacing(10)
            
            # Colored label
            ant_label = BodyLabel(f"ANT {i + 1}", self)
            ant_label.setStyleSheet(f"color: {colors[i]}; font-weight: bold;")
            ant_label.setFixedWidth(50)
            ant_layout.addWidget(ant_label)
            
            # SpinBox with BLACK text (not green)
            spinbox = SpinBox(self)
            spinbox.setRange(0, 33)
            spinbox.setValue(30)
            spinbox.setSuffix(" dBm")
            spinbox.setFixedHeight(40)
            spinbox.setMinimumWidth(140)
            # STYLE FIX: Force black text color
            spinbox.setStyleSheet("""
                SpinBox {
                    color: #000000;
                }
                SpinBox LineEdit {
                    color: #000000;
                }
            """)
            self.ant_spinboxes.append(spinbox)
            ant_layout.addWidget(spinbox)
            
            ant_layout.addStretch()
            ant_grid.addLayout(ant_layout, row, col)
        
        main_layout.addLayout(ant_grid)
        
        # ─── Apply Button (RIGHT ALIGNED, not full width) ─────
        btn_row = QHBoxLayout()
        btn_row.addStretch()  # CRITICAL: Push button to the right
        
        self.apply_per_ant_btn = PrimaryPushButton("Apply Settings", self, FIF.ACCEPT)
        self.apply_per_ant_btn.setFixedHeight(40)
        self.apply_per_ant_btn.setFixedWidth(140)  # Fixed width prevents "blue bar"
        btn_row.addWidget(self.apply_per_ant_btn)
        
        main_layout.addLayout(btn_row)
        
        # ─── Signal Connections ───────────────────────────────
        self.set_all_btn.clicked.connect(self._on_set_all)
        self.apply_per_ant_btn.clicked.connect(self._on_apply_per_antenna)
        self.get_power_btn.clicked.connect(self.get_power.emit)
    
    def _on_set_all(self):
        power_text = self.power_combo.currentText()
        power_value = int(power_text.split()[0])
        self.set_power.emit(power_value)
    
    def _on_apply_per_antenna(self):
        values = [spin.value() for spin in self.ant_spinboxes]
        self.set_power_per_antenna.emit(values[0], values[1], values[2], values[3])
    
    def update_power(self, powers: list):
        """Update UI from reader response"""
        if powers and len(powers) > 0:
            self.power_combo.setCurrentIndex(min(powers[0], 33))
            for i, power in enumerate(powers[:4]):
                if i < len(self.ant_spinboxes):
                    self.ant_spinboxes[i].setValue(power)


# ============================================================
# FREQUENCY CARD - Region & Frequency Selection (EXPANDED)
# ============================================================
class FrequencyCard(CardWidget):
    """
    Configure frequency region settings.
    
    Layout:
    - Row 1: RadioButtons for region selection (US, China, Vietnam, Manual)
    - Row 2: Start/End frequency ComboBoxes (enabled when Manual selected)
    - Row 3: Action buttons (Get/Set Frequency) aligned right
    """
    
    set_frequency = pyqtSignal(str)
    get_frequency = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # ─── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)
        
        icon = IconWidget(FIF.WIFI, self)
        icon.setFixedSize(24, 24)
        header.addWidget(icon)
        
        title = StrongBodyLabel("Frequency Region", self)
        header.addWidget(title)
        header.addStretch()
        
        main_layout.addLayout(header)
        
        # ─── Row 1: Region Selection RadioButtons ─────────────
        region_label = BodyLabel("Select Region:", self)
        region_label.setStyleSheet("font-weight: 600;")
        main_layout.addWidget(region_label)
        
        region_row = QHBoxLayout()
        region_row.setSpacing(20)
        
        self.region_group = QButtonGroup(self)
        self.region_radios = {}
        
        regions = [
            ('US', 'US (902-928 MHz)'),
            ('CHINA', 'China (920-925 MHz)'),
            ('VIETNAM', 'Vietnam (918-923 MHz)'),
            ('MANUAL', 'Manual'),
        ]
        
        for i, (key, label) in enumerate(regions):
            radio = RadioButton(label, self)
            radio.setMinimumHeight(38)
            self.region_group.addButton(radio, i)
            self.region_radios[key] = radio
            region_row.addWidget(radio)
        
        self.region_radios['US'].setChecked(True)
        region_row.addStretch()
        main_layout.addLayout(region_row)
        
        # ─── Row 2: Manual Frequency Selection ────────────────
        freq_label = CaptionLabel("Manual Frequency Range (enabled when 'Manual' is selected):", self)
        freq_label.setStyleSheet("color: #666;")
        main_layout.addWidget(freq_label)
        
        freq_row = QHBoxLayout()
        freq_row.setSpacing(16)
        
        # Start Frequency
        freq_row.addWidget(BodyLabel("Start:", self))
        self.start_freq_combo = ComboBox(self)
        frequencies = [f"{902.0 + i * 0.5:.1f} MHz" for i in range(53)]
        self.start_freq_combo.addItems(frequencies)
        self.start_freq_combo.setCurrentIndex(0)
        self.start_freq_combo.setFixedHeight(40)
        self.start_freq_combo.setMinimumWidth(130)
        self.start_freq_combo.setEnabled(False)
        freq_row.addWidget(self.start_freq_combo)
        
        freq_row.addSpacing(20)
        
        # End Frequency
        freq_row.addWidget(BodyLabel("End:", self))
        self.end_freq_combo = ComboBox(self)
        self.end_freq_combo.addItems(frequencies)
        self.end_freq_combo.setCurrentIndex(52)
        self.end_freq_combo.setFixedHeight(40)
        self.end_freq_combo.setMinimumWidth(130)
        self.end_freq_combo.setEnabled(False)
        freq_row.addWidget(self.end_freq_combo)
        
        freq_row.addStretch()
        main_layout.addLayout(freq_row)
        
        # ─── Row 3: Action Buttons (Right Aligned) ────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.get_freq_btn = PushButton("Get Frequency", self, FIF.SYNC)
        self.get_freq_btn.setFixedHeight(40)
        self.get_freq_btn.setFixedWidth(130)
        btn_row.addWidget(self.get_freq_btn)
        
        self.set_freq_btn = PrimaryPushButton("Set Frequency", self, FIF.ACCEPT)
        self.set_freq_btn.setFixedHeight(40)
        self.set_freq_btn.setFixedWidth(130)
        btn_row.addWidget(self.set_freq_btn)
        
        main_layout.addLayout(btn_row)
        
        # ─── Signal Connections ───────────────────────────────
        self.region_radios['MANUAL'].toggled.connect(self._on_manual_toggled)
        self.set_freq_btn.clicked.connect(self._on_set_frequency)
        self.get_freq_btn.clicked.connect(self.get_frequency.emit)
    
    def _on_manual_toggled(self, checked: bool):
        """Enable/disable frequency combos based on Manual selection"""
        self.start_freq_combo.setEnabled(checked)
        self.end_freq_combo.setEnabled(checked)
    
    def _on_set_frequency(self):
        """Emit set_frequency signal with selected region"""
        for key, radio in self.region_radios.items():
            if radio.isChecked():
                self.set_frequency.emit(key)
                return


# ============================================================
# RF LINK PROFILE CARD
# ============================================================
class RFLinkCard(CardWidget):
    """RF Link Profile selection"""
    
    set_profile = pyqtSignal(int)
    get_profile = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        icon = IconWidget(FIF.LINK, self)
        icon.setFixedSize(24, 24)
        header.addWidget(icon)
        header.addWidget(StrongBodyLabel("RF Link Profile", self))
        header.addStretch()
        main_layout.addLayout(header)
        
        # Profile Grid
        profile_grid = QGridLayout()
        profile_grid.setVerticalSpacing(10)
        profile_grid.setHorizontalSpacing(20)
        
        self.profile_radios = []
        profiles = [
            (0xD0, "Profile 0", "Tari 25μs, FM0, LF=40KHz"),
            (0xD1, "Profile 1", "Tari 25μs, Miller 4, LF=250KHz"),
            (0xD2, "Profile 2", "Tari 25μs, Miller 4, LF=300KHz"),
            (0xD3, "Profile 3", "Tari 6.25μs, FM0, LF=400KHz"),
        ]
        
        for i, (code, name, desc) in enumerate(profiles):
            radio = RadioButton(name, self)
            radio.setProperty('code', code)
            radio.setMinimumHeight(36)
            self.profile_radios.append(radio)
            profile_grid.addWidget(radio, i, 0)
            
            desc_label = CaptionLabel(desc, self)
            desc_label.setStyleSheet("color: #666;")
            profile_grid.addWidget(desc_label, i, 1)
        
        self.profile_radios[0].setChecked(True)
        main_layout.addLayout(profile_grid)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.get_profile_btn = PushButton("Get Profile", self, FIF.SYNC)
        self.get_profile_btn.setFixedHeight(40)
        btn_row.addWidget(self.get_profile_btn)
        
        self.set_profile_btn = PrimaryPushButton("Set Profile", self, FIF.ACCEPT)
        self.set_profile_btn.setFixedHeight(40)
        self.set_profile_btn.setFixedWidth(120)
        btn_row.addWidget(self.set_profile_btn)
        
        main_layout.addLayout(btn_row)
        
        # Connections
        self.set_profile_btn.clicked.connect(self._on_set_profile)
        self.get_profile_btn.clicked.connect(self.get_profile.emit)
    
    def _on_set_profile(self):
        for radio in self.profile_radios:
            if radio.isChecked():
                self.set_profile.emit(radio.property('code'))
                return
    
    def set_profile_selection(self, code: int):
        for radio in self.profile_radios:
            if radio.property('code') == code:
                radio.setChecked(True)
                return


# ============================================================
# BEEPER CARD
# ============================================================
class BeeperCard(CardWidget):
    """Beeper on/off control"""
    
    set_beeper = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        
        icon = IconWidget(FIF.VOLUME, self)
        icon.setFixedSize(24, 24)
        layout.addWidget(icon)
        
        layout.addWidget(StrongBodyLabel("Beeper", self))
        layout.addStretch()
        
        self.switch = SwitchButton(self)
        self.switch.setOnText("On")
        self.switch.setOffText("Off")
        layout.addWidget(self.switch)
        
        self.apply_btn = PrimaryPushButton("Apply", self, FIF.ACCEPT)
        self.apply_btn.setFixedHeight(36)
        self.apply_btn.setFixedWidth(80)
        self.apply_btn.clicked.connect(lambda: self.set_beeper.emit(self.switch.isChecked()))
        layout.addWidget(self.apply_btn)


# ============================================================
# MAIN SETTINGS PAGE
# ============================================================
class SettingsPage(QWidget):
    """
    Main Settings Page with scrollable content.
    
    CRITICAL: setObjectName("settingsPage") must be called for navigation.
    """
    
    # Signals for controller connection
    get_firmware = pyqtSignal()
    get_reader_id = pyqtSignal()
    get_temperature = pyqtSignal()
    set_power = pyqtSignal(int)
    set_power_per_antenna = pyqtSignal(int, int, int, int)
    get_power = pyqtSignal()
    set_frequency = pyqtSignal(str)
    get_frequency = pyqtSignal()
    set_rf_profile = pyqtSignal(int)
    get_rf_profile = pyqtSignal()
    set_beeper = pyqtSignal(bool)
    reset_reader = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # CRITICAL: Object name for navigation system
        self.setObjectName("settingsPage")
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for Raspberry Pi screens
        scroll = SmoothScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        # Content widget
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        scroll.setWidget(content)
        
        # Content layout
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 20, 30, 30)
        
        # ─── Title ────────────────────────────────────────────
        title = StrongBodyLabel("Reader Settings", self)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        layout.addWidget(title)
        
        subtitle = CaptionLabel("Configure RFID reader parameters", self)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # ─── Row 1: Info + Power ──────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        
        self.info_card = InfoCard()
        self.power_card = PowerCard()
        
        # Connect InfoCard signals
        self.info_card.get_firmware_btn.clicked.connect(self.get_firmware.emit)
        self.info_card.get_reader_id_btn.clicked.connect(self.get_reader_id.emit)
        self.info_card.get_temperature_btn.clicked.connect(self.get_temperature.emit)
        
        # Connect PowerCard signals
        self.power_card.set_power.connect(self.set_power.emit)
        self.power_card.set_power_per_antenna.connect(self.set_power_per_antenna.emit)
        self.power_card.get_power.connect(self.get_power.emit)
        
        row1.addWidget(self.info_card, 2)
        row1.addWidget(self.power_card, 3)
        layout.addLayout(row1)
        
        # ─── Row 2: Frequency (Full Width) ────────────────────
        self.freq_card = FrequencyCard()
        self.freq_card.set_frequency.connect(self.set_frequency.emit)
        self.freq_card.get_frequency.connect(self.get_frequency.emit)
        layout.addWidget(self.freq_card)
        
        # ─── Row 3: RF Link + Beeper/Reset ────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        
        self.rf_card = RFLinkCard()
        self.rf_card.set_profile.connect(self.set_rf_profile.emit)
        self.rf_card.get_profile.connect(self.get_rf_profile.emit)
        
        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        
        self.beeper_card = BeeperCard()
        self.beeper_card.set_beeper.connect(self.set_beeper.emit)
        
        # Reset card
        reset_card = CardWidget()
        reset_layout = QHBoxLayout(reset_card)
        reset_layout.setContentsMargins(20, 16, 20, 16)
        
        reset_icon = IconWidget(FIF.UPDATE, reset_card)
        reset_icon.setFixedSize(24, 24)
        reset_layout.addWidget(reset_icon)
        reset_layout.addWidget(StrongBodyLabel("Reset Reader", reset_card))
        reset_layout.addStretch()
        
        self.reset_btn = PushButton("Reset", reset_card, FIF.SYNC)
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.clicked.connect(self.reset_reader.emit)
        reset_layout.addWidget(self.reset_btn)
        
        right_col.addWidget(self.beeper_card)
        right_col.addWidget(reset_card)
        
        row3.addWidget(self.rf_card, 2)
        row3.addLayout(right_col, 1)
        layout.addLayout(row3)
        
        layout.addStretch()
        outer_layout.addWidget(scroll)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable all settings controls based on connection state"""
        self.info_card.setEnabled(enabled)
        self.power_card.setEnabled(enabled)
        self.freq_card.setEnabled(enabled)
        self.rf_card.setEnabled(enabled)
        self.beeper_card.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
    
    def update_reader_info(self, info: dict):
        """Update all cards from reader response"""
        self.info_card.update_info(info)
        
        if 'powers' in info:
            self.power_card.update_power(info['powers'])
        
        if 'rf_profile' in info:
            self.rf_card.set_profile_selection(info['rf_profile'])
