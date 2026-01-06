"""
Connection Page - Serial Port Connection Management
Windows 11 Fluent Design

CROSS-PLATFORM SUPPORT:
- Windows: Shows COM ports (COM1, COM2, etc.)
- Linux/Pi: Shows /dev/ttyUSB*, /dev/ttyACM*, etc.
- Includes auto-detect feature for RFID readers
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QSpacerItem, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import sys
import os

from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    ComboBox, PrimaryPushButton, PushButton, 
    TextEdit, IconWidget, InfoBar, InfoBarPosition,
    FluentIcon as FIF, ProgressRing, IndeterminateProgressRing
)

# Platform detection
IS_LINUX = sys.platform.startswith('linux')
IS_RASPBERRY_PI = IS_LINUX and os.path.exists('/proc/device-tree/model')


class ConnectionCard(CardWidget):
    """Card for serial port connection settings"""
    
    connect_clicked = pyqtSignal(str, int)  # port, baudrate
    disconnect_clicked = pyqtSignal()
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._is_connected = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        icon = IconWidget(FIF.CONNECT, self)
        icon.setFixedSize(24, 24)
        title_label = StrongBodyLabel(self._title, self)
        title_layout.addWidget(icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Status indicator
        self.status_label = CaptionLabel("Disconnected", self)
        self.status_label.setStyleSheet("color: #F44336;")
        title_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        
        # Form grid
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        # Serial Port - Cross-platform label
        # Windows shows "COM Port", Linux shows "Serial Port"
        port_label_text = "Serial Port:" if IS_LINUX else "COM Port:"
        port_label = BodyLabel(port_label_text, self)
        self.port_combo = ComboBox(self)
        self.port_combo.setMinimumWidth(200)
        
        # Platform-specific placeholder
        if IS_LINUX:
            self.port_combo.setPlaceholderText("e.g., /dev/ttyUSB0")
        else:
            self.port_combo.setPlaceholderText("Select COM port")
        
        # Auto-detect button (especially useful on Pi)
        self.auto_detect_btn = PushButton("Auto", self)
        self.auto_detect_btn.setFixedWidth(60)
        self.auto_detect_btn.setToolTip("Auto-detect RFID reader port")
        self.auto_detect_btn.clicked.connect(self._on_auto_detect)
        
        # Baud Rate
        baud_label = BodyLabel("Baud Rate:", self)
        self.baud_combo = ComboBox(self)
        self.baud_combo.setMinimumWidth(200)
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '230400'])
        self.baud_combo.setCurrentIndex(4)  # Default 115200 (matches C#)
        
        form_layout.addWidget(port_label, 0, 0)
        form_layout.addWidget(self.port_combo, 0, 1)
        form_layout.addWidget(self.auto_detect_btn, 0, 2)
        form_layout.addWidget(baud_label, 1, 0)
        form_layout.addWidget(self.baud_combo, 1, 1)
        form_layout.setColumnStretch(3, 1)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.refresh_btn = PushButton("Refresh Ports", self, FIF.SYNC)
        self.connect_btn = PrimaryPushButton("Connect", self, FIF.LINK)
        self.disconnect_btn = PushButton("Disconnect", self, FIF.CANCEL)
        self.disconnect_btn.setEnabled(False)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(btn_layout)
        
        # Connect signals
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
    
    def _on_auto_detect(self):
        """Auto-detect RFID reader port"""
        try:
            from utils import detect_rfid_reader_port
            detected = detect_rfid_reader_port()
            if detected:
                # Add to combo if not present
                if self.port_combo.findText(detected) == -1:
                    self.port_combo.addItem(detected)
                self.port_combo.setCurrentText(detected)
            else:
                # Show tooltip/status that no reader was detected
                InfoBar.warning(
                    title="Auto-Detect",
                    content="No RFID reader detected. Is it connected?",
                    parent=self.window(),
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
        except ImportError:
            pass  # Auto-detect not available
    
    def _on_connect(self):
        """Handle connect button click"""
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        if port:
            self.connect_clicked.emit(port, baud)
    
    def _on_disconnect(self):
        """Handle disconnect button click"""
        self.disconnect_clicked.emit()
    
    def set_ports(self, ports: list):
        """Set available ports"""
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
    
    def set_connected(self, connected: bool):
        """Update connection state"""
        self._is_connected = connected
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.port_combo.setEnabled(not connected)
        self.baud_combo.setEnabled(not connected)
        
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: #F44336;")


class LogCard(CardWidget):
    """Card for log output display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup log card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_layout = QHBoxLayout()
        icon = IconWidget(FIF.HISTORY, self)
        icon.setFixedSize(24, 24)
        title = StrongBodyLabel("Operation Log", self)
        
        self.clear_btn = PushButton("Clear", self, FIF.DELETE)
        self.clear_btn.setFixedWidth(80)
        
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.clear_btn)
        
        layout.addLayout(title_layout)
        
        # Log text area
        self.log_text = TextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setStyleSheet("""
            TextEdit {
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                background-color: #1E1E1E;
                color: #D4D4D4;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # Connect clear button
        self.clear_btn.clicked.connect(self.log_text.clear)
    
    def append_log(self, message: str, log_type: int = 0):
        """Append message to log with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if log_type == 0:  # Normal
            color = "#D4D4D4"
        elif log_type == 1:  # Error
            color = "#F44336"
        elif log_type == 2:  # Success
            color = "#4CAF50"
        else:
            color = "#2196F3"  # Info
        
        html = f'<span style="color: #808080;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        self.log_text.append(html.strip())


class ConnectionPage(QWidget):
    """Connection management page"""
    
    connect_reader = pyqtSignal(str, int)
    disconnect_reader = pyqtSignal()
    connect_sensor = pyqtSignal(str, int)
    disconnect_sensor = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("connectionPage")
        self._setup_ui()
        self.refresh_ports()
    
    def _setup_ui(self):
        """Setup the page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(36, 20, 36, 20)
        
        # Page title with logo in header
        header_layout = QHBoxLayout()
        
        # Left side: Title and subtitle container
        title_container = QVBoxLayout()
        title_container.setSpacing(4)
        
        title = StrongBodyLabel("Connection Settings", self)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        title_container.addWidget(title)
        
        subtitle = CaptionLabel("Configure serial port connections for RFID reader and sensors", self)
        subtitle.setStyleSheet("color: #666;")
        title_container.addWidget(subtitle)
        
        # Add title container to header
        header_layout.addLayout(title_container)
        
        # Center stretch to push logo to the right
        header_layout.addStretch()
        
        # Right side: Logo
        logo_label = QLabel(self)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo-nextwaves.png')
        
        if os.path.exists(logo_path):
            # Load image at high quality
            pixmap = QPixmap(logo_path)
            
            # Set device pixel ratio for high DPI displays
            device_ratio = self.devicePixelRatioF()
            pixmap.setDevicePixelRatio(device_ratio)
            
            # Scale logo to 100px height for balanced visibility
            scaled_pixmap = pixmap.scaledToHeight(
                int(100 * device_ratio),
                Qt.TransformationMode.SmoothTransformation
            )
            scaled_pixmap.setDevicePixelRatio(device_ratio)
            
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            logo_label.setFixedHeight(108)
            logo_label.setFixedWidth(173)
            logo_label.setScaledContents(True)
            logo_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    padding: 8px;
                    border-radius: 6px;
                }
            """)
        
        header_layout.addWidget(logo_label)
        header_layout.setContentsMargins(0, 0, 0, 15)
        
        layout.addLayout(header_layout)
        
        # Connection cards in horizontal layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Reader connection card
        self.reader_card = ConnectionCard("RFID Reader Connection", self)
        self.reader_card.connect_clicked.connect(self.connect_reader.emit)
        self.reader_card.disconnect_clicked.connect(self.disconnect_reader.emit)
        self.reader_card.refresh_btn.clicked.connect(self.refresh_ports)
        
        # Sensor connection card
        self.sensor_card = ConnectionCard("Sensor Connection", self)
        self.sensor_card.connect_clicked.connect(self.connect_sensor.emit)
        self.sensor_card.disconnect_clicked.connect(self.disconnect_sensor.emit)
        self.sensor_card.refresh_btn.clicked.connect(self.refresh_ports)
        
        cards_layout.addWidget(self.reader_card)
        cards_layout.addWidget(self.sensor_card)
        
        layout.addLayout(cards_layout)
        
        # Log card
        self.log_card = LogCard(self)
        layout.addWidget(self.log_card, 1)  # Stretch factor 1
    
    def refresh_ports(self):
        """
        Refresh available serial ports
        
        CROSS-PLATFORM:
        - Uses improved port detection from serial_utils
        - On Linux/Pi: Shows /dev/ttyUSB*, /dev/ttyACM*, etc.
        - On Windows: Shows COM1, COM2, etc.
        """
        try:
            # Try to use the improved port detection from utils
            try:
                from utils import get_available_ports
                ports = get_available_ports()
            except ImportError:
                # Fallback to direct serial.tools.list_ports
                import serial.tools.list_ports
                ports = [p.device for p in serial.tools.list_ports.comports()]
            
            self.reader_card.set_ports(ports)
            self.sensor_card.set_ports(ports)
            
            # Log platform info
            if IS_RASPBERRY_PI:
                platform_note = "Raspberry Pi detected"
            elif IS_LINUX:
                platform_note = "Linux detected"
            else:
                platform_note = "Windows detected"
            
            if ports:
                self.append_log(f"Found {len(ports)} port(s) ({platform_note})", 0)
            else:
                self.append_log(f"No serial ports found ({platform_note})", 1)
                
        except Exception as e:
            self.append_log(f"Error refreshing ports: {e}", 1)
    
    def set_connected(self, connected: bool, message: str = ""):
        """Update connection state"""
        self.reader_card.set_connected(connected)
        if message:
            log_type = 2 if connected else 1
            self.append_log(message, log_type)
    
    def append_log(self, message: str, log_type: int = 0):
        """Append message to log"""
        self.log_card.append_log(message, log_type)

