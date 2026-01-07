"""
GPIO Control Page
Windows 11 Fluent Design
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QPixmap, QCursor, QDesktopServices
import os

from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    PrimaryPushButton, PushButton, RadioButton,
    IconWidget, SwitchButton, ToggleButton,
    FluentIcon as FIF
)

# Import responsive UI configuration
from utils.ui_config import get_ui_config


class GPIOCard(CardWidget):
    """Card for a single GPIO pin control"""
    
    state_changed = pyqtSignal(int, bool)  # gpio_num, state
    
    def __init__(self, gpio_num: int, parent=None):
        super().__init__(parent)
        self._gpio_num = gpio_num
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Title
        title_layout = QHBoxLayout()
        
        # GPIO icon (using a colored indicator)
        self.indicator = QFrame(self)
        self.indicator.setFixedSize(16, 16)
        self.indicator.setStyleSheet("""
            QFrame {
                background-color: #9E9E9E;
                border-radius: 8px;
            }
        """)
        title_layout.addWidget(self.indicator)
        
        title = StrongBodyLabel(f"GPIO {self._gpio_num}", self)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Status
        self.status_label = BodyLabel("OFF", self)
        self.status_label.setStyleSheet("color: #9E9E9E; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Control buttons
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)
        
        self.off_btn = RadioButton("OFF", self)
        self.on_btn = RadioButton("ON", self)
        self.off_btn.setChecked(True)
        
        self.off_btn.toggled.connect(self._on_state_toggled)
        
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.off_btn)
        ctrl_layout.addWidget(self.on_btn)
        ctrl_layout.addStretch()
        
        layout.addLayout(ctrl_layout)
    
    def _on_state_toggled(self, off_checked: bool):
        """Handle state toggle"""
        is_on = not off_checked
        self._update_visual(is_on)
        self.state_changed.emit(self._gpio_num, is_on)
    
    def _update_visual(self, is_on: bool):
        """Update visual appearance based on state"""
        if is_on:
            self.indicator.setStyleSheet("""
                QFrame {
                    background-color: #4CAF50;
                    border-radius: 8px;
                }
            """)
            self.status_label.setText("ON")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 24px; font-weight: bold;")
        else:
            self.indicator.setStyleSheet("""
                QFrame {
                    background-color: #9E9E9E;
                    border-radius: 8px;
                }
            """)
            self.status_label.setText("OFF")
            self.status_label.setStyleSheet("color: #9E9E9E; font-size: 24px; font-weight: bold;")
    
    def set_state(self, is_on: bool, update_buttons: bool = True):
        """Set GPIO state"""
        if update_buttons:
            self.on_btn.setChecked(is_on)
            self.off_btn.setChecked(not is_on)
        self._update_visual(is_on)
    
    @property
    def gpio_num(self) -> int:
        return self._gpio_num
    
    @property
    def is_on(self) -> bool:
        return self.on_btn.isChecked()


class S11MeasurementCard(CardWidget):
    """Card for S11 (Return Loss) measurement"""
    
    measure_requested = pyqtSignal(int)  # frequency index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Title
        title_layout = QHBoxLayout()
        icon = IconWidget(FIF.CALORIES, self)
        icon.setFixedSize(24, 24)
        title = StrongBodyLabel("Antenna Return Loss (S11)", self)
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Measurement controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(BodyLabel("Frequency:", self))
        
        from qfluentwidgets import ComboBox
        self.freq_combo = ComboBox(self)
        # Add frequency options (simplified)
        freqs = [f"{902 + i * 2:.0f} MHz" for i in range(14)]
        self.freq_combo.addItems(freqs)
        self.freq_combo.setCurrentIndex(0)
        ctrl_layout.addWidget(self.freq_combo)
        
        ctrl_layout.addStretch()
        
        self.measure_btn = PrimaryPushButton("Measure", self, FIF.SEND)
        self.measure_btn.clicked.connect(self._on_measure)
        ctrl_layout.addWidget(self.measure_btn)
        
        layout.addLayout(ctrl_layout)
        
        # Result display
        result_layout = QHBoxLayout()
        result_layout.addWidget(BodyLabel("Return Loss:", self))
        
        self.result_label = StrongBodyLabel("-- dB", self)
        self.result_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.result_label.setStyleSheet("color: #0078D4;")
        result_layout.addWidget(self.result_label)
        result_layout.addStretch()
        
        layout.addLayout(result_layout)
    
    def _on_measure(self):
        self.measure_requested.emit(self.freq_combo.currentIndex())
    
    def set_result(self, value: float):
        """Set the measurement result"""
        self.result_label.setText(f"{value:.1f} dB")


class GPIOPage(QWidget):
    """GPIO control page"""
    
    # Signals
    gpio_changed = pyqtSignal(int, bool)  # gpio_num, state
    read_gpio = pyqtSignal()
    write_gpio = pyqtSignal(dict)  # {gpio_num: state}
    measure_s11 = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("gpioPage")
        self._gpio_cards = []
        self.logo_label = None
        self._setup_ui()

    def refresh_logo(self):
        """Refresh the header logo based on current theme"""
        from qfluentwidgets import isDarkTheme
        if self.logo_label is None:
            return
        logo_filename = 'logo-nextwaves.png' if isDarkTheme() else 'logo-nextwaves_.png'
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), logo_filename)
        if not os.path.exists(logo_path):
            return
        pixmap = QPixmap(logo_path)
        device_ratio = self.devicePixelRatioF()
        pixmap.setDevicePixelRatio(device_ratio)
        scaled_pixmap = pixmap.scaledToHeight(
            int(get_ui_config().logo_height * device_ratio),
            Qt.TransformationMode.SmoothTransformation
        )
        scaled_pixmap.setDevicePixelRatio(device_ratio)
        self.logo_label.setPixmap(scaled_pixmap)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(36, 20, 36, 20)
        
        # Get UI config
        from utils.ui_config import get_ui_config
        ui_config = get_ui_config()
        
        # Page title with logo header
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title = StrongBodyLabel("GPIO Control", self)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        title_container.addWidget(title)
        
        subtitle = CaptionLabel("Control GPIO pins and measure antenna return loss", self)
        subtitle.setStyleSheet("color: #666;")
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # Add logo on the right
        if ui_config.show_logo_in_header:
            self.logo_label = QLabel(self)
            
            # Use different logo for light/dark mode
            from qfluentwidgets import isDarkTheme
            logo_filename = 'logo-nextwaves.png' if isDarkTheme() else 'logo-nextwaves_.png'
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), logo_filename)
            
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                device_ratio = self.devicePixelRatioF()
                pixmap.setDevicePixelRatio(device_ratio)
                scaled_pixmap = pixmap.scaledToHeight(
                    int(ui_config.logo_height * device_ratio),
                    Qt.TransformationMode.SmoothTransformation
                )
                scaled_pixmap.setDevicePixelRatio(device_ratio)
                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.logo_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                self.logo_label.setToolTip("Visit NextWaves.com")
                self.logo_label.mousePressEvent = lambda event: QDesktopServices.openUrl(QUrl("https://nextwaves.com/"))
                header_layout.addWidget(self.logo_label)
        
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # GPIO cards grid
        gpio_layout = QHBoxLayout()
        gpio_layout.setSpacing(16)
        
        for i in range(1, 5):
            card = GPIOCard(i, self)
            card.state_changed.connect(self.gpio_changed.emit)
            self._gpio_cards.append(card)
            gpio_layout.addWidget(card)
        
        layout.addLayout(gpio_layout)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.read_btn = PushButton("Read GPIO States", self, FIF.SYNC)
        self.read_btn.clicked.connect(self.read_gpio.emit)
        
        self.write_btn = PrimaryPushButton("Write GPIO States", self, FIF.ACCEPT)
        self.write_btn.clicked.connect(self._on_write)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.read_btn)
        btn_layout.addWidget(self.write_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # S11 measurement card
        self.s11_card = S11MeasurementCard(self)
        self.s11_card.measure_requested.connect(self.measure_s11.emit)
        layout.addWidget(self.s11_card)
        
        layout.addStretch()
    
    def _on_write(self):
        """Emit write signal with current states"""
        states = {}
        for card in self._gpio_cards:
            states[card.gpio_num] = card.is_on
        self.write_gpio.emit(states)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable controls"""
        for card in self._gpio_cards:
            card.setEnabled(enabled)
        self.read_btn.setEnabled(enabled)
        self.write_btn.setEnabled(enabled)
        self.s11_card.setEnabled(enabled)
    
    def update_gpio_state(self, states: dict):
        """
        Update GPIO states
        states: {gpio_num: bool}
        """
        for card in self._gpio_cards:
            if card.gpio_num in states:
                card.set_state(states[card.gpio_num])
    
    def set_s11_result(self, value: float):
        """Set S11 measurement result"""
        self.s11_card.set_result(value)

