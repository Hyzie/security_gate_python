"""
Reader Controller
Connects models and views, handles business logic flow

RASPBERRY PI OPTIMIZATIONS:
- Batched UI updates to reduce rendering load on Pi GPU
- Thread-safe tag queue instead of immediate signal emission
- Configurable update intervals (100ms default)
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog
from datetime import datetime
import threading
from collections import deque
import sys

from models import ReaderModel, SensorDirection, RXInventoryTag
from utils import SerialManager, ConnectionParams, ExcelExporter, ReaderProtocol

# =============================================================================
# RASPBERRY PI UI OPTIMIZATION CONSTANTS
# =============================================================================

# Platform detection for adaptive UI updates
IS_LINUX = sys.platform.startswith('linux')
IS_RASPBERRY_PI = IS_LINUX and __import__('os').path.exists('/proc/device-tree/model')

# UI update interval in milliseconds
# On Pi, we batch updates every 150ms to reduce GPU/CPU load
# On desktop, we can update more frequently (50ms)
if IS_RASPBERRY_PI:
    UI_UPDATE_INTERVAL_MS = 150  # Raspberry Pi: update 6-7 times/second
elif IS_LINUX:
    UI_UPDATE_INTERVAL_MS = 100  # Linux desktop: 10 times/second
else:
    UI_UPDATE_INTERVAL_MS = 50   # Windows/Mac: 20 times/second

# Maximum tags to process per UI update batch
# Prevents UI freeze if many tags arrive at once
MAX_TAGS_PER_UPDATE = 50


class ReaderController(QObject):
    """
    Main controller that coordinates the application
    Connects the Model (business logic) with the View (UI)
    
    RASPBERRY PI OPTIMIZATIONS:
    - Uses batched UI updates via QTimer instead of per-tag signals
    - Thread-safe tag queue for decoupling serial thread from UI thread
    - Dirty flag mechanism to skip unnecessary UI updates
    """
    
    # Signals for thread-safe UI updates
    log_message = pyqtSignal(str, int)  # message, type
    tag_received = pyqtSignal(dict)  # Kept for compatibility, but batched
    tags_batch_received = pyqtSignal(list)  # New: batch of tags for efficiency
    counts_updated = pyqtSignal(int, int)  # unique, total
    detected_tags_updated = pyqtSignal(list)
    connection_changed = pyqtSignal(bool, str)
    reader_info_updated = pyqtSignal(dict)
    gpio_state_updated = pyqtSignal(dict)
    
    def __init__(self, view):
        super().__init__()
        
        self._view = view
        self._model = ReaderModel()
        self._serial = SerialManager()
        
        self._is_inventory_running = False
        self._inventory_thread = None
        self._response_buffer = bytearray()
        
        # Antenna configuration for FastSwitchInventory (0x8A command)
        # Format: [Stay][Count] pairs for 4 antennas + 2 reserved bytes
        # Stay = antenna dwell time (0x00-0x03), Count = 0x01 enabled, 0x00 disabled
        # Default: ANT1 and ANT2 enabled
        self._antenna_config = bytearray([
            0x00, 0x01,  # ANT1: stay=0, enabled
            0x01, 0x01,  # ANT2: stay=1, enabled
            0x02, 0x00,  # ANT3: stay=2, disabled
            0x03, 0x00,  # ANT4: stay=3, disabled
            0x00, 0x00   # Reserved
        ])
        
        # =====================================================
        # RASPBERRY PI: Batched UI update system
        # Instead of updating UI for every tag, we queue tags
        # and update UI in batches via QTimer
        # =====================================================
        self._tag_queue = deque(maxlen=1000)  # Thread-safe queue
        self._tag_queue_lock = threading.Lock()
        self._counts_dirty = False  # Flag to indicate counts need update
        self._last_unique_count = 0
        self._last_total_count = 0
        
        # Timer for batched UI updates
        self._ui_update_timer = QTimer(self)
        self._ui_update_timer.setInterval(UI_UPDATE_INTERVAL_MS)
        self._ui_update_timer.timeout.connect(self._flush_ui_updates)
        
        self._setup_connections()
        self._setup_model_callbacks()
    
    def _setup_connections(self):
        """Connect view signals to controller slots"""
        # Connection page
        self._view.connection_page.connect_reader.connect(self.connect_reader)
        self._view.connection_page.disconnect_reader.connect(self.disconnect_reader)
        self._view.connection_page.connect_sensor.connect(self.connect_sensor)
        self._view.connection_page.disconnect_sensor.connect(self.disconnect_sensor)
        
        # Inventory page
        self._view.inventory_page.start_inventory.connect(self.start_inventory)
        self._view.inventory_page.stop_inventory.connect(self.stop_inventory)
        self._view.inventory_page.clear_data.connect(self.clear_data)
        self._view.inventory_page.export_data.connect(self.export_data)
        
        # Settings page
        self._view.settings_page.get_firmware.connect(self.get_firmware)
        self._view.settings_page.get_reader_id.connect(self.get_reader_id)
        self._view.settings_page.get_temperature.connect(self.get_temperature)
        self._view.settings_page.set_power.connect(self.set_power)
        self._view.settings_page.set_power_per_antenna.connect(self.set_power_per_antenna)
        self._view.settings_page.get_power.connect(self.get_power)
        self._view.settings_page.set_frequency.connect(self.set_frequency)
        self._view.settings_page.get_frequency.connect(self.get_frequency)
        self._view.settings_page.set_rf_profile.connect(self.set_rf_profile)
        self._view.settings_page.get_rf_profile.connect(self.get_rf_profile)
        self._view.settings_page.set_beeper.connect(self.set_beeper)
        self._view.settings_page.reset_reader.connect(self.reset_reader)
        
        # GPIO page
        self._view.gpio_page.read_gpio.connect(self.read_gpio)
        self._view.gpio_page.write_gpio.connect(self.write_gpio)
        self._view.gpio_page.measure_s11.connect(self.measure_s11)
        
        # Controller signals to view
        self.log_message.connect(self._view.append_log)
        self.connection_changed.connect(self._view.set_connected_state)
        self.tag_received.connect(self._on_tag_received_ui)
        self.tags_batch_received.connect(self._on_tags_batch_received_ui)  # Pi optimization
        self.counts_updated.connect(self._view.update_tag_counts)
        self.detected_tags_updated.connect(self._view.update_detected_tags)
        self.reader_info_updated.connect(self._view.update_reader_info)
        self.gpio_state_updated.connect(self._view.update_gpio_state)
    
    def _setup_model_callbacks(self):
        """Setup callbacks from model"""
        self._model.set_callbacks(
            on_tag=self._on_tag_detected,
            on_sensor=self._on_sensor_triggered,
            on_log=lambda msg: self.log_message.emit(msg, 0)
        )
        
        # Setup serial callbacks
        self._serial.set_callbacks(
            on_data=self._on_data_received,
            on_sensor=self._on_sensor_data,
            on_cts=self._on_cts_changed,
            on_dsr=self._on_dsr_changed,
            on_error=lambda msg: self.log_message.emit(msg, 1)
        )
    
    # ============================================================
    # RASPBERRY PI: Batched UI Update System
    # ============================================================
    
    def _flush_ui_updates(self):
        """
        Flush queued tag updates to UI in batches
        
        Called by QTimer at UI_UPDATE_INTERVAL_MS intervals.
        This prevents overwhelming the Pi's GPU with constant updates.
        
        OPTIMIZATION: Only updates UI if there are actual changes.
        """
        if not self._is_inventory_running:
            return
        
        # Collect tags from queue (up to MAX_TAGS_PER_UPDATE)
        tags_to_update = []
        with self._tag_queue_lock:
            for _ in range(min(len(self._tag_queue), MAX_TAGS_PER_UPDATE)):
                if self._tag_queue:
                    tags_to_update.append(self._tag_queue.popleft())
        
        # Update UI with batched tags
        if tags_to_update:
            # Emit batch signal for efficient processing
            self.tags_batch_received.emit(tags_to_update)
        
        # Update counts only if changed (dirty flag optimization)
        if self._counts_dirty:
            current_unique = self._model.epc_count
            current_total = self._model.total_tag_count
            
            # Only emit if actually changed
            if current_unique != self._last_unique_count or current_total != self._last_total_count:
                self._last_unique_count = current_unique
                self._last_total_count = current_total
                self.counts_updated.emit(current_unique, current_total)
            
            self._counts_dirty = False
    
    def _queue_tag_for_ui(self, tag_dict: dict):
        """
        Queue a tag for batched UI update instead of immediate emission
        
        Thread-safe: can be called from serial read thread
        """
        with self._tag_queue_lock:
            self._tag_queue.append(tag_dict)
        self._counts_dirty = True
    
    # ============================================================
    # Connection Methods
    # ============================================================
    
    @pyqtSlot(str, int)
    def connect_reader(self, port: str, baudrate: int):
        """Connect to RFID reader"""
        params = ConnectionParams(port=port, baudrate=baudrate)
        success, message = self._serial.connect_reader(params)
        
        self.connection_changed.emit(success, message)
        self.log_message.emit(message, 2 if success else 1)
    
    @pyqtSlot()
    def disconnect_reader(self):
        """Disconnect from reader"""
        if self._is_inventory_running:
            self.stop_inventory()
        
        success, message = self._serial.disconnect_reader()
        self.connection_changed.emit(False, message)
        self.log_message.emit(message, 0)
    
    @pyqtSlot(str, int)
    def connect_sensor(self, port: str, baudrate: int):
        """Connect to sensor port"""
        params = ConnectionParams(port=port, baudrate=baudrate)
        success, message = self._serial.connect_sensor(params)
        self.log_message.emit(message, 2 if success else 1)
    
    @pyqtSlot()
    def disconnect_sensor(self):
        """Disconnect sensor port"""
        success, message = self._serial.disconnect_sensor()
        self.log_message.emit(message, 0)
    
    # ============================================================
    # Inventory Methods
    # ============================================================
    
    @pyqtSlot(dict)
    def start_inventory(self, config: dict):
        """Start inventory operation"""
        if self._is_inventory_running:
            return
        
        if not self._serial.is_reader_connected:
            self.log_message.emit("Reader not connected", 1)
            return
        
        # Update antenna configuration
        # Format: [Stay][Count] for each antenna (4 antennas + 2 reserved bytes = 10 bytes)
        # Stay = dwell time per antenna (0x00-0x03 recommended, higher = longer dwell)
        # Count = 0x01 to enable, 0x00 to disable
        # IMPORTANT: Using 0xFF as stay causes reader to skip that antenna!
        antennas = config.get('antennas', [True, True, False, False])
        
        # Build config with consistent stay values for all enabled antennas
        self._antenna_config = bytearray([
            0x00, 0x01 if antennas[0] else 0x00,  # ANT1: stay=0, enabled?
            0x01, 0x01 if antennas[1] else 0x00,  # ANT2: stay=1, enabled?
            0x02, 0x01 if antennas[2] else 0x00,  # ANT3: stay=2, enabled?
            0x03, 0x01 if antennas[3] else 0x00,  # ANT4: stay=3, enabled?
            0x00, 0x00  # Reserved
        ])
        
        # Log which antennas are enabled
        enabled = [f"ANT{i+1}" for i, en in enumerate(antennas) if en]
        self.log_message.emit(f"Antennas enabled: {', '.join(enabled) if enabled else 'None'}", 0)
        
        self._is_inventory_running = True
        self._view.set_inventory_running(True)
        
        # Clear the tag queue before starting
        with self._tag_queue_lock:
            self._tag_queue.clear()
        self._counts_dirty = False
        
        # Start the UI update timer (RASPBERRY PI OPTIMIZATION)
        # This batches UI updates instead of updating per-tag
        self._ui_update_timer.start()
        
        # Start inventory thread
        self._inventory_thread = threading.Thread(
            target=self._inventory_loop, 
            daemon=True,
            name="InventoryLoop"
        )
        self._inventory_thread.start()
        
        platform_info = " (Pi optimized)" if IS_RASPBERRY_PI else ""
        self.log_message.emit(f"Inventory started{platform_info}", 2)
    
    @pyqtSlot()
    def stop_inventory(self):
        """Stop inventory operation"""
        self._is_inventory_running = False
        
        # Stop the UI update timer safely (must be on main thread)
        if self._ui_update_timer.isActive():
            self._ui_update_timer.stop()
        
        # Flush any remaining tags to UI
        self._flush_ui_updates()
        
        if self._inventory_thread:
            self._inventory_thread.join(timeout=2.0)
            self._inventory_thread = None
        
        self._view.set_inventory_running(False)
        self.log_message.emit("Inventory stopped", 0)
        
        # Analyze detected tags
        self._analyze_and_update()
    
    def _inventory_loop(self):
        """
        Background inventory loop
        
        RASPBERRY PI OPTIMIZATION:
        Uses longer delay between commands to reduce CPU load
        and give the reader time to respond properly.
        """
        import time
        
        # Inventory command interval
        # Pi: 80ms gives ~12 scans/sec (plenty for RFID)
        # Desktop: 50ms gives ~20 scans/sec
        scan_interval = 0.080 if IS_RASPBERRY_PI else 0.050
        
        while self._is_inventory_running:
            # Send fast switch inventory command
            cmd = ReaderProtocol.build_fast_switch_inventory(0xFF, bytes(self._antenna_config))
            self._serial.send_command(cmd)
            
            # Delay between scans - critical for Pi stability
            time.sleep(scan_interval)
    
    @pyqtSlot()
    def clear_data(self):
        """Clear all inventory data"""
        self._model.clear_data()
        self.counts_updated.emit(0, 0)
        self.log_message.emit("Data cleared", 0)
    
    @pyqtSlot()
    def export_data(self):
        """Export data to Excel"""
        if not ExcelExporter.is_available():
            self.log_message.emit("Excel export not available. Install openpyxl.", 1)
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self._view,
            "Export Data",
            ExcelExporter.generate_filename("rfid_inventory"),
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            data = self._model.get_history_for_export()
            success, message = ExcelExporter.export_read_history(data, filename)
            self.log_message.emit(message, 2 if success else 1)
    
    # ============================================================
    # Data Processing
    # ============================================================
    
    def _on_data_received(self, data: bytes):
        """Handle data received from reader"""
        self._response_buffer.extend(data)
        self._process_buffer()
    
    def _process_buffer(self):
        """Process the response buffer for complete frames"""
        while len(self._response_buffer) >= 5:
            # Look for frame start
            if self._response_buffer[0] != 0xA0:
                self._response_buffer.pop(0)
                continue
            
            # Check if we have complete frame
            frame_len = self._response_buffer[1]
            if len(self._response_buffer) < frame_len + 2:
                break  # Wait for more data
            
            # Extract frame
            frame = bytes(self._response_buffer[:frame_len + 2])
            self._response_buffer = self._response_buffer[frame_len + 2:]
            
            # Parse and process
            self._process_frame(frame)
    
    def _process_frame(self, frame: bytes):
        """
        Process a complete response frame
        
        RASPBERRY PI OPTIMIZATION:
        Instead of emitting signals for each tag, we queue them
        for batched UI updates. This dramatically reduces CPU/GPU
        load on the Pi.
        """
        result = ReaderProtocol.parse_response(frame)
        
        if not result['valid']:
            return
        
        cmd = result['cmd']
        data = result['data']
        
        # Handle fast switch inventory response
        if cmd == 0x8A and self._is_inventory_running:
            tag_data = ReaderProtocol.parse_tag_data(cmd, data)
            if tag_data and tag_data['epc']:
                tag = RXInventoryTag(
                    str_epc=tag_data['epc'],
                    str_rssi=str(tag_data['rssi']),
                    bt_ant_id=tag_data['antenna'],
                    str_freq=tag_data['frequency'],
                    str_pc=tag_data['pc']
                )
                self._model.process_tag(tag)
                
                # RASPBERRY PI OPTIMIZATION:
                # Queue tag for batched UI update instead of immediate emission
                # The _flush_ui_updates() method will emit signals in batches
                self._queue_tag_for_ui({
                    'epc': tag_data['epc'],
                    'antenna': tag_data['antenna'],
                    'count': self._model.get_tag_count(tag_data['epc']),
                    'rssi': tag_data['rssi'],
                    'frequency': tag_data['frequency']
                })
                # Don't emit counts_updated here - handled by _flush_ui_updates()
        
        # Handle other responses
        elif cmd == 0x72:  # Firmware version
            if len(data) >= 2:
                fw = f"{data[0]}.{data[1]}"
                self.reader_info_updated.emit({'firmware': fw})
        
        elif cmd == 0x68:  # Reader ID
            reader_id = data.hex().upper()
            self.reader_info_updated.emit({'reader_id': reader_id})
        
        elif cmd == 0x7B:  # Temperature
            if len(data) >= 2:
                sign = "" if data[0] != 0 else "-"
                temp = f"{sign}{data[1]}°C"
                self.reader_info_updated.emit({'temperature': temp})
        
        elif cmd == 0x76:  # Set Power response
            # Response from SET power command
            # data[0] == 0x10 means success, other values are error codes
            if len(data) >= 1:
                if data[0] == 0x10:
                    self.log_message.emit("Power set successfully", 2)
                else:
                    self.log_message.emit(f"Set power failed: error 0x{data[0]:02X}", 1)
        
        elif cmd == 0x77 or cmd == 0x97:  # Get Power response
            # Response from GET power command (0x77=4-ant, 0x97=8-ant)
            powers = list(data[:4]) if len(data) >= 4 else list(data)
            self.reader_info_updated.emit({'powers': powers})
            self.log_message.emit(f"Power levels: {powers} dBm", 0)
        
        elif cmd == 0x6A:  # RF Profile
            if data:
                self.reader_info_updated.emit({'rf_profile': data[0]})
        
        elif cmd == 0x60:  # GPIO read
            if len(data) >= 2:
                self.gpio_state_updated.emit({
                    1: data[0] != 0,
                    2: data[1] != 0,
                    3: data[2] != 0 if len(data) > 2 else False,
                    4: data[3] != 0 if len(data) > 3 else False
                })
        
        elif cmd == 0x7E:  # S11 measurement
            if data:
                self._view.gpio_page.set_s11_result(data[0])
    
    def _on_tag_detected(self, tag: RXInventoryTag):
        """Called when model detects a tag"""
        pass  # Handled in _process_frame
    
    def _on_tag_received_ui(self, tag_dict: dict):
        """Update UI with single tag data (called from main thread)"""
        self._view.inventory_page.add_tag(tag_dict)
    
    def _on_tags_batch_received_ui(self, tags_list: list):
        """
        Update UI with batch of tags (RASPBERRY PI OPTIMIZATION)
        
        Called from main thread via signal. Processes multiple tags
        in a single UI update cycle, which is much more efficient
        than updating per-tag on resource-constrained devices.
        """
        # Use batch update method if available, otherwise fall back to single updates
        if hasattr(self._view.inventory_page, 'add_tags_batch'):
            self._view.inventory_page.add_tags_batch(tags_list)
        else:
            # Fallback: update one by one but in a tight loop (still faster than separate signals)
            for tag_dict in tags_list:
                self._view.inventory_page.add_tag(tag_dict)
    
    def _on_sensor_triggered(self, direction: SensorDirection, time_diff: float):
        """Called when sensor direction is determined"""
        self.log_message.emit(f"Sensor triggered: {direction.name} ({time_diff:.1f}ms)", 3)
        
        # Stop inventory and analyze
        if self._is_inventory_running:
            self.stop_inventory()
    
    def _analyze_and_update(self):
        """Analyze tags and update detected list"""
        results = self._model.analyze_tags()
        self.detected_tags_updated.emit(results)
    
    # ============================================================
    # Sensor Handling
    # ============================================================
    
    def _on_sensor_data(self, text: str):
        """Handle sensor port data"""
        self.log_message.emit(f"Sensor: {text.strip()}", 0)
        
        now = datetime.now()
        if "#1" in text:
            self._model.handle_sensor_activation(True, now)
        if "#2" in text:
            self._model.handle_sensor_activation(False, now)
    
    def _on_cts_changed(self, state: bool, timestamp: datetime):
        """Handle CTS pin change (Sensor 1)"""
        if state:
            self._model.handle_sensor_activation(True, timestamp)
    
    def _on_dsr_changed(self, state: bool, timestamp: datetime):
        """Handle DSR pin change (Sensor 2)"""
        if state:
            self._model.handle_sensor_activation(False, timestamp)
    
    # ============================================================
    # Reader Commands
    # ============================================================
    
    @pyqtSlot()
    def get_firmware(self):
        """Get reader firmware version"""
        cmd = ReaderProtocol.build_get_firmware(0xFF)
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting firmware version...", 0)
    
    @pyqtSlot()
    def get_reader_id(self):
        """Get reader identifier"""
        cmd = ReaderProtocol.build_get_reader_id(0xFF)
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting reader ID...", 0)
    
    @pyqtSlot()
    def get_temperature(self):
        """Get reader temperature"""
        cmd = ReaderProtocol.build_get_temperature(0xFF)
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting temperature...", 0)
    
    @pyqtSlot(int)
    def set_power(self, power_dbm: int):
        """
        Set output power
        
        Protocol (from C# ReaderMethod.cs):
        - Command: 0x76
        - Data: Single byte with dBm value (0-33)
        - Response: 0x10 = success, other = error
        """
        try:
            # Validate range
            if not 0 <= power_dbm <= 33:
                self.log_message.emit(f"Power must be 0-33 dBm, got {power_dbm}", 1)
                return
            
            cmd = ReaderProtocol.build_set_power(0xFF, power_dbm)
            if self._serial.send_command(cmd):
                self.log_message.emit(f"Setting power to {power_dbm} dBm...", 0)
            else:
                self.log_message.emit("Failed to send power command", 1)
        except ValueError as e:
            self.log_message.emit(str(e), 1)
    
    @pyqtSlot()
    def get_power(self):
        """
        Get output power levels for all antennas
        
        C# uses 0x97 (GetOutputPower) which returns power for ALL antennas
        0x77 (GetOutputPowerFour) only returns single/current antenna power
        """
        # Use 0x97 to get all antenna powers (matches C# GetOutputPower)
        cmd = ReaderProtocol.build_get_power(0xFF, eight_antenna=True)
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting power settings...", 0)
    
    @pyqtSlot(int, int, int, int)
    def set_power_per_antenna(self, ant1: int, ant2: int, ant3: int, ant4: int):
        """
        Set output power per antenna (for multi-antenna configurations)
        
        Args:
            ant1-ant4: Power level in dBm (0-33) for each antenna
        """
        try:
            cmd = ReaderProtocol.build_set_power_per_antenna(0xFF, ant1, ant2, ant3, ant4)
            if self._serial.send_command(cmd):
                self.log_message.emit(f"Setting per-antenna power: [{ant1}, {ant2}, {ant3}, {ant4}] dBm...", 0)
            else:
                self.log_message.emit("Failed to send power command", 1)
        except ValueError as e:
            self.log_message.emit(str(e), 1)
    
    @pyqtSlot(str)
    def set_frequency(self, region: str):
        """Set frequency region"""
        regions = {
            'US': (0x01, 0x07, 0x3B),
            'CHINA': (0x01, 0x2B, 0x35),
            'VIETNAM': (0x01, 0x27, 0x31),
        }
        
        if region in regions:
            code, start, end = regions[region]
            cmd = ReaderProtocol.build_set_frequency_region(0xFF, code, start, end)
            if self._serial.send_command(cmd):
                self.log_message.emit(f"Setting frequency region: {region}", 0)
    
    @pyqtSlot()
    def get_frequency(self):
        """Get frequency region"""
        cmd = ReaderProtocol.create_frame(0xFF, 0x79, b'')
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting frequency region...", 0)
    
    @pyqtSlot(int)
    def set_rf_profile(self, profile: int):
        """Set RF link profile"""
        cmd = ReaderProtocol.build_set_rf_profile(0xFF, profile)
        if self._serial.send_command(cmd):
            self.log_message.emit(f"Setting RF profile: 0x{profile:02X}", 0)
    
    @pyqtSlot()
    def get_rf_profile(self):
        """Get RF link profile"""
        cmd = ReaderProtocol.create_frame(0xFF, 0x6A, b'')
        if self._serial.send_command(cmd):
            self.log_message.emit("Getting RF profile...", 0)
    
    @pyqtSlot(bool)
    def set_beeper(self, enabled: bool):
        """Set beeper mode"""
        mode = 2 if enabled else 0
        cmd = ReaderProtocol.build_set_beeper_mode(0xFF, mode)
        if self._serial.send_command(cmd):
            self.log_message.emit(f"Setting beeper: {'ON' if enabled else 'OFF'}", 0)
    
    @pyqtSlot()
    def reset_reader(self):
        """Reset the reader"""
        cmd = ReaderProtocol.build_reset_reader(0xFF)
        if self._serial.send_command(cmd):
            self.log_message.emit("Resetting reader...", 0)
    
    @pyqtSlot()
    def read_gpio(self):
        """Read GPIO values"""
        cmd = ReaderProtocol.create_frame(0xFF, 0x60, b'')
        if self._serial.send_command(cmd):
            self.log_message.emit("Reading GPIO states...", 0)
    
    @pyqtSlot(dict)
    def write_gpio(self, states: dict):
        """Write GPIO values"""
        for gpio_num, state in states.items():
            value = 1 if state else 0
            cmd = ReaderProtocol.create_frame(0xFF, 0x61, bytes([gpio_num, value]))
            self._serial.send_command(cmd)
        self.log_message.emit("GPIO states written", 0)
    
    @pyqtSlot(int)
    def measure_s11(self, freq_index: int):
        """Measure antenna return loss"""
        cmd = ReaderProtocol.create_frame(0xFF, 0x7E, bytes([freq_index]))
        if self._serial.send_command(cmd):
            self.log_message.emit("Measuring S11...", 0)
    
    # ============================================================
    # Cleanup
    # ============================================================
    
    def cleanup(self):
        """Cleanup resources"""
        self._is_inventory_running = False
        if self._inventory_thread:
            self._inventory_thread.join(timeout=2.0)
        self._serial.cleanup()

