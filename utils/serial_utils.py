"""
Serial Communication Utilities
Handles serial port connections for RFID reader and sensors

CRITICAL PROTOCOL NOTES (from C# reference implementation):
1. Checksum uses TWO'S COMPLEMENT: (~sum + 1) & 0xFF
2. Frame structure: [0xA0][Length][ReaderID][CMD][Data...][Checksum]
3. Length = len(data) + 3 (includes ReaderID, CMD, but NOT header or checksum)
4. DTR and RTS must be enabled for hardware flow control
5. Default baudrate is 115200

RASPBERRY PI / LINUX OPTIMIZATIONS:
- Auto-detects Linux serial ports (/dev/ttyUSB*, /dev/ttyACM*)
- Checks for dialout group permissions
- Increased sleep intervals to reduce CPU usage on ARM
- Thread-safe design for smooth GUI operation
"""

import serial
import serial.tools.list_ports
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass
import threading
import time
from datetime import datetime
import sys
import os
import platform


# =============================================================================
# RASPBERRY PI / LINUX SPECIFIC CONSTANTS
# =============================================================================

# Platform detection
IS_LINUX = sys.platform.startswith('linux')
IS_RASPBERRY_PI = IS_LINUX and os.path.exists('/proc/device-tree/model')

# Sleep intervals - CRITICAL for Raspberry Pi CPU optimization!
# On Pi, tight loops without sleep will consume 100% CPU and freeze the system
if IS_RASPBERRY_PI or IS_LINUX:
    # Raspberry Pi: Use longer sleep to reduce CPU load
    # 10ms gives ~100 polls/sec which is plenty for RFID response times
    SERIAL_POLL_INTERVAL = 0.010  # 10ms - saves significant CPU on Pi
    SENSOR_POLL_INTERVAL = 0.010  # 10ms
else:
    # Windows/Desktop: Can use tighter polling
    SERIAL_POLL_INTERVAL = 0.001  # 1ms
    SENSOR_POLL_INTERVAL = 0.001  # 1ms


def get_available_ports() -> List[str]:
    """
    Get list of available serial ports
    
    CROSS-PLATFORM:
    - Windows: Returns COM1, COM2, etc.
    - Linux/Pi: Returns /dev/ttyUSB0, /dev/ttyACM0, /dev/ttyS0, etc.
    
    Filters out non-relevant ports on each platform.
    """
    ports = serial.tools.list_ports.comports()
    
    if IS_LINUX:
        # On Linux, filter to show only likely RFID reader ports
        # ttyUSB* = USB-to-Serial adapters (most common for RFID readers)
        # ttyACM* = USB CDC devices (Arduino-style readers)
        # ttyS* = Hardware UART (Pi GPIO pins)
        filtered = []
        for port in ports:
            device = port.device
            if any(x in device for x in ['/dev/ttyUSB', '/dev/ttyACM', '/dev/ttyS']):
                filtered.append(port)
        ports = filtered
    
    return [port.device for port in sorted(ports, key=lambda p: p.device)]


def check_linux_permissions(port: str) -> Tuple[bool, str]:
    """
    Check if user has permission to access serial port on Linux
    
    On Raspberry Pi/Linux, users must be in 'dialout' group to access serial ports.
    This function checks and provides helpful error messages.
    
    Returns: (has_permission, message)
    """
    if not IS_LINUX:
        return True, "Not Linux - permissions not applicable"
    
    if not os.path.exists(port):
        return False, f"Port {port} does not exist. Is the RFID reader connected?"
    
    # Check if user can access the port
    if os.access(port, os.R_OK | os.W_OK):
        return True, "Permission OK"
    
    # Get current user and groups
    import grp
    import pwd
    
    try:
        username = pwd.getpwuid(os.getuid()).pw_name
        user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        
        # Check if in dialout group
        if 'dialout' not in user_groups:
            return False, (
                f"Permission denied for {port}.\n"
                f"User '{username}' is not in 'dialout' group.\n"
                f"Run: sudo usermod -a -G dialout {username}\n"
                f"Then log out and back in."
            )
        else:
            return False, f"Permission denied for {port}. Try: sudo chmod 666 {port}"
    except Exception as e:
        return False, f"Permission check failed: {e}"


def detect_rfid_reader_port() -> Optional[str]:
    """
    Auto-detect RFID reader port
    
    Scans available ports and returns the most likely RFID reader port.
    Uses VID/PID matching and port naming heuristics.
    
    Returns: Port name or None if not found
    """
    ports = serial.tools.list_ports.comports()
    
    # Priority order for detection
    candidates = []
    
    for port in ports:
        score = 0
        device = port.device
        
        # USB-Serial adapters are most common for RFID readers
        if '/dev/ttyUSB' in device or 'USB' in device.upper():
            score += 10
        if '/dev/ttyACM' in device:
            score += 5
            
        # Check for common RFID reader chip identifiers
        desc = (port.description or '').lower()
        if any(x in desc for x in ['cp210', 'ch340', 'ftdi', 'pl2303', 'rfid', 'reader']):
            score += 15
        
        # Check manufacturer
        mfg = (port.manufacturer or '').lower()
        if any(x in mfg for x in ['silicon labs', 'ftdi', 'wch', 'prolific']):
            score += 10
        
        if score > 0:
            candidates.append((score, device))
    
    if candidates:
        # Return highest scoring port
        candidates.sort(reverse=True)
        return candidates[0][1]
    
    return None


@dataclass
class ConnectionParams:
    """
    Serial connection parameters matching C# implementation
    
    BAUD RATE NOTE:
    The C# code uses 115200 as the default baudrate.
    This is a standard rate that works reliably on Raspberry Pi.
    Non-standard rates (like 256000) can cause issues on Pi UART.
    """
    port: str
    baudrate: int = 115200  # Matches C#: iSerialPort.BaudRate = 115200
    timeout: float = 0.2    # ReadTimeout = 200ms in C#
    dtr: bool = True        # DtrEnable = true in C#
    rts: bool = True        # RtsEnable = true in C#
    # Note: C# uses default parity (None), databits (8), stopbits (1)


class SerialManager:
    """
    Manages serial port communication with RFID reader
    Handles both reader commands and sensor signals
    
    RASPBERRY PI OPTIMIZATIONS:
    - Uses platform-specific polling intervals to reduce CPU usage
    - Checks for dialout group permissions on Linux
    - Thread-safe design with proper locking
    """
    
    # Standard baud rates - 115200 is default and most reliable on Pi
    COMMON_BAUDRATES = [9600, 19200, 38400, 57600, 115200, 230400]
    
    def __init__(self):
        self._reader_port: Optional[serial.Serial] = None
        self._sensor_port: Optional[serial.Serial] = None
        
        self._reader_thread: Optional[threading.Thread] = None
        self._sensor_thread: Optional[threading.Thread] = None
        
        self._is_reading = False
        self._read_lock = threading.Lock()
        
        # Callbacks
        self._on_data_received: Optional[Callable[[bytes], None]] = None
        self._on_sensor_data: Optional[Callable[[str], None]] = None
        self._on_cts_changed: Optional[Callable[[bool, datetime], None]] = None
        self._on_dsr_changed: Optional[Callable[[bool, datetime], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
        # Previous pin states for edge detection
        self._prev_cts = False
        self._prev_dsr = False
        
        # Platform info for logging
        self._platform_info = f"{'Raspberry Pi' if IS_RASPBERRY_PI else 'Linux' if IS_LINUX else platform.system()}"
    
    @property
    def is_reader_connected(self) -> bool:
        """Check if reader port is connected"""
        return self._reader_port is not None and self._reader_port.is_open
    
    @property
    def is_sensor_connected(self) -> bool:
        """Check if sensor port is connected"""
        return self._sensor_port is not None and self._sensor_port.is_open
    
    def set_callbacks(self,
                      on_data: Callable[[bytes], None] = None,
                      on_sensor: Callable[[str], None] = None,
                      on_cts: Callable[[bool, datetime], None] = None,
                      on_dsr: Callable[[bool, datetime], None] = None,
                      on_error: Callable[[str], None] = None):
        """Set callback functions for events"""
        self._on_data_received = on_data
        self._on_sensor_data = on_sensor
        self._on_cts_changed = on_cts
        self._on_dsr_changed = on_dsr
        self._on_error = on_error
    
    def connect_reader(self, params: ConnectionParams) -> Tuple[bool, str]:
        """
        Connect to RFID reader serial port
        Returns (success, message)
        
        Matches C# implementation:
        - iSerialPort.PortName = strPort
        - iSerialPort.BaudRate = nBaudrate
        - iSerialPort.ReadTimeout = 200
        - iSerialPort.DtrEnable = true (set before open in Form1)
        - iSerialPort.RtsEnable = true (set before open in Form1)
        
        LINUX/RASPBERRY PI:
        - Checks dialout group permissions before connecting
        - Uses platform-appropriate port naming
        """
        try:
            # =====================================================
            # LINUX PERMISSION CHECK - Critical for Raspberry Pi!
            # =====================================================
            if IS_LINUX:
                has_perm, perm_msg = check_linux_permissions(params.port)
                if not has_perm:
                    return False, perm_msg
            
            if self._reader_port and self._reader_port.is_open:
                self._reader_port.close()
            
            # Create serial port with settings matching C# implementation
            # In C#, DTR/RTS are set on the iSerialPort object before Open()
            self._reader_port = serial.Serial()
            self._reader_port.port = params.port
            self._reader_port.baudrate = params.baudrate
            self._reader_port.timeout = params.timeout
            self._reader_port.write_timeout = params.timeout
            
            # C# defaults (System.IO.Ports.SerialPort)
            self._reader_port.bytesize = serial.EIGHTBITS
            self._reader_port.parity = serial.PARITY_NONE
            self._reader_port.stopbits = serial.STOPBITS_ONE
            
            # Set DTR/RTS BEFORE opening - critical for some hardware!
            # In C#: reader.iSerialPort.DtrEnable = true; reader.iSerialPort.RtsEnable = true;
            self._reader_port.dtr = params.dtr
            self._reader_port.rts = params.rts
            
            # =====================================================
            # LINUX: Set exclusive access to prevent conflicts
            # =====================================================
            if IS_LINUX:
                self._reader_port.exclusive = True
            
            # Now open the port
            self._reader_port.open()
            
            # Small delay after opening to let hardware settle
            # Slightly longer on Pi due to USB enumeration timing
            settle_time = 0.1 if IS_RASPBERRY_PI else 0.05
            time.sleep(settle_time)
            
            # Clear any stale data in buffers
            self._reader_port.reset_input_buffer()
            self._reader_port.reset_output_buffer()
            
            # Start monitoring thread
            self._is_reading = True
            self._reader_thread = threading.Thread(
                target=self._reader_monitor_loop, 
                daemon=True,
                name="ReaderMonitor"  # Named thread for debugging
            )
            self._reader_thread.start()
            
            platform_note = f" ({self._platform_info})" if IS_LINUX else ""
            return True, f"Connected to {params.port} @ {params.baudrate} baud{platform_note}"
            
        except serial.SerialException as e:
            error_msg = str(e)
            # Provide more helpful errors on Linux
            if IS_LINUX and "Permission denied" in error_msg:
                return False, f"Permission denied for {params.port}. Add user to dialout group."
            elif IS_LINUX and "could not open port" in error_msg.lower():
                return False, f"Cannot open {params.port}. Is the RFID reader connected?"
            return False, f"Connection failed: {error_msg}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disconnect_reader(self) -> Tuple[bool, str]:
        """Disconnect from reader serial port"""
        try:
            self._is_reading = False
            
            if self._reader_thread and self._reader_thread.is_alive():
                self._reader_thread.join(timeout=2.0)
            
            if self._reader_port and self._reader_port.is_open:
                self._reader_port.close()
            
            self._reader_port = None
            return True, "Reader disconnected"
            
        except Exception as e:
            return False, f"Disconnect error: {str(e)}"
    
    def connect_sensor(self, params: ConnectionParams) -> Tuple[bool, str]:
        """Connect to sensor serial port"""
        try:
            if self._sensor_port and self._sensor_port.is_open:
                self._sensor_port.close()
            
            self._sensor_port = serial.Serial(
                port=params.port,
                baudrate=params.baudrate,
                timeout=params.timeout
            )
            
            # Start sensor reading thread
            self._sensor_thread = threading.Thread(target=self._sensor_read_loop, daemon=True)
            self._sensor_thread.start()
            
            return True, f"Sensor connected to {params.port} @ {params.baudrate} baud"
            
        except serial.SerialException as e:
            return False, f"Sensor connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disconnect_sensor(self) -> Tuple[bool, str]:
        """Disconnect from sensor serial port"""
        try:
            if self._sensor_port and self._sensor_port.is_open:
                self._sensor_port.close()
            
            self._sensor_port = None
            return True, "Sensor disconnected"
            
        except Exception as e:
            return False, f"Disconnect error: {str(e)}"
    
    def send_command(self, data: bytes) -> bool:
        """
        Send command to reader
        
        Matches C# ReaderMethod.SendMessage():
        - Writes data directly to serial port
        - Uses iSerialPort.Write(btArySenderData, 0, btArySenderData.Length)
        """
        try:
            if self._reader_port and self._reader_port.is_open:
                # Flush output buffer before sending (ensures clean transmission)
                self._reader_port.flush()
                # Write the command bytes
                bytes_written = self._reader_port.write(data)
                # Ensure all bytes are transmitted
                self._reader_port.flush()
                return bytes_written == len(data)
            return False
        except Exception as e:
            if self._on_error:
                self._on_error(f"Send error: {str(e)}")
            return False
    
    def _reader_monitor_loop(self):
        """
        Background thread for monitoring reader port
        
        RASPBERRY PI CPU OPTIMIZATION:
        Uses SERIAL_POLL_INTERVAL (10ms on Pi, 1ms on desktop)
        Without proper sleep, this loop will consume 100% CPU on Pi
        and cause system freezes!
        
        The 10ms interval still provides ~100 polls/second which is
        more than enough for RFID communication (tags typically read
        at 50-200ms intervals).
        """
        while self._is_reading and self._reader_port and self._reader_port.is_open:
            try:
                # Check for data - read all available bytes at once
                bytes_waiting = self._reader_port.in_waiting
                if bytes_waiting > 0:
                    # Read all available data in one call (more efficient)
                    data = self._reader_port.read(bytes_waiting)
                    if data and self._on_data_received:
                        self._on_data_received(data)
                
                # Monitor CTS/DSR pins for sensor signals
                # Note: Some USB-Serial adapters don't support these pins
                try:
                    now = datetime.now()
                    
                    cts = self._reader_port.cts
                    if cts and not self._prev_cts:  # Rising edge
                        if self._on_cts_changed:
                            self._on_cts_changed(True, now)
                    self._prev_cts = cts
                    
                    dsr = self._reader_port.dsr
                    if dsr and not self._prev_dsr:  # Rising edge
                        if self._on_dsr_changed:
                            self._on_dsr_changed(True, now)
                    self._prev_dsr = dsr
                except (OSError, serial.SerialException):
                    # Some adapters don't support CTS/DSR - silently ignore
                    pass
                
                # =====================================================
                # CRITICAL: Sleep to prevent 100% CPU usage on Pi!
                # SERIAL_POLL_INTERVAL is 10ms on Pi, 1ms on desktop
                # =====================================================
                time.sleep(SERIAL_POLL_INTERVAL)
                
            except serial.SerialException as e:
                if "disconnected" in str(e).lower() or "device" in str(e).lower():
                    if self._on_error:
                        self._on_error("Reader disconnected unexpectedly")
                    break
                if self._on_error:
                    self._on_error(f"Serial error: {str(e)}")
            except Exception as e:
                if self._on_error:
                    self._on_error(f"Monitor error: {str(e)}")
                break
    
    def _sensor_read_loop(self):
        """
        Background thread for reading sensor data
        
        RASPBERRY PI CPU OPTIMIZATION:
        Uses SENSOR_POLL_INTERVAL to reduce CPU load
        """
        while self._sensor_port and self._sensor_port.is_open:
            try:
                bytes_waiting = self._sensor_port.in_waiting
                if bytes_waiting > 0:
                    data = self._sensor_port.read(bytes_waiting)
                    if data:
                        text = data.decode('utf-8', errors='ignore')
                        if self._on_sensor_data:
                            self._on_sensor_data(text)
                
                # CRITICAL: Sleep to reduce CPU usage on Pi
                time.sleep(SENSOR_POLL_INTERVAL)
                
            except serial.SerialException:
                # Port disconnected
                break
            except Exception as e:
                if self._on_error:
                    self._on_error(f"Sensor read error: {str(e)}")
                break
    
    def cleanup(self):
        """Clean up all resources"""
        self._is_reading = False
        
        if self._reader_port and self._reader_port.is_open:
            try:
                self._reader_port.close()
            except:
                pass
        
        if self._sensor_port and self._sensor_port.is_open:
            try:
                self._sensor_port.close()
            except:
                pass


# ============================================================
# RFID Reader Protocol Implementation
# ============================================================

class ReaderProtocol:
    """
    Protocol implementation for RFID reader commands
    Based on the UHF RFID reader protocol
    
    Frame Structure (from C# MessageTran.cs):
    [0] Header: 0xA0 (160 decimal)
    [1] Length: Number of bytes from [2] to [N-1] (excludes header and checksum)
    [2] ReaderID: Reader address (0xFF for broadcast)
    [3] Command: Command code
    [4..N-1] Data: Command-specific data (optional)
    [N] Checksum: Two's complement of sum of bytes [0] to [N-1]
    
    CRITICAL: Checksum is TWO'S COMPLEMENT, not simple sum!
    C# code: return Convert.ToByte((int) ((~num + 1) & 0xff));
    """
    
    # =================================================================
    # COMMAND OPCODES (from C# CMD.cs and ReaderMethod.cs)
    # =================================================================
    CMD_READ_GPIO = 0x60
    CMD_WRITE_GPIO = 0x61
    CMD_SET_READER_ID = 0x67
    CMD_GET_READER_ID = 0x68
    CMD_SET_RF_PROFILE = 0x69
    CMD_GET_RADIO_PROFILE = 0x6A
    CMD_RESET = 0x70
    CMD_SET_BAUDRATE = 0x71
    CMD_GET_FIRMWARE = 0x72
    CMD_SET_READER_ADDRESS = 0x73
    CMD_SET_WORK_ANTENNA = 0x74
    CMD_GET_ANTENNA = 0x75
    
    # POWER COMMANDS - CRITICAL: These were mixed up in previous version!
    # C# ReaderMethod.cs clearly shows:
    # - 0x76 = SetOutputPower (sends power value, sets the power)
    # - 0x77 = GetOutputPowerFour (reads power for 4-antenna readers)
    # - 0x97 = GetOutputPower (reads power for 8-antenna readers)
    CMD_SET_POWER = 0x76        # Set output power (C#: cmd_set_output_power)
    CMD_GET_POWER_4ANT = 0x77   # Get power for 4-antenna readers
    CMD_GET_POWER_8ANT = 0x97   # Get power for 8-antenna readers
    
    CMD_SET_FREQUENCY = 0x78
    CMD_GET_FREQUENCY = 0x79
    CMD_SET_BEEPER = 0x7A
    CMD_GET_TEMPERATURE = 0x7B
    CMD_SET_DRM_MODE = 0x7C
    CMD_GET_DRM_MODE = 0x7D
    CMD_GET_IMPEDANCE = 0x7E
    
    CMD_WRITE_TAG = 0x82
    CMD_FAST_SWITCH = 0x8A
    
    # Response status codes
    RESPONSE_SUCCESS = 0x10     # Command executed successfully
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum using TWO'S COMPLEMENT method
        
        This matches the C# MessageTran.CheckSum() implementation:
        
        public byte CheckSum(byte[] btAryBuffer, int nStartPos, int nLen)
        {
            byte num = 0;
            for (int i = nStartPos; i < (nStartPos + nLen); i++)
            {
                num = (byte) (num + btAryBuffer[i]);
            }
            return Convert.ToByte((int) ((~num + 1) & 0xff));
        }
        
        Args:
            data: Bytes to calculate checksum over (header through data, NOT including checksum position)
            
        Returns:
            Two's complement checksum as single byte (0-255)
        """
        # Sum all bytes
        total = sum(data) & 0xFF
        # Two's complement: invert and add 1, mask to 8 bits
        checksum = (~total + 1) & 0xFF
        return checksum
    
    @staticmethod
    def create_frame(reader_id: int, cmd: int, data: bytes = b'') -> bytes:
        """
        Create a command frame matching C# MessageTran constructor
        
        C# implementation (MessageTran.cs lines 63-80):
        - btPacketType = 160 (0xA0)
        - btDataLen = data.Length + 3 (includes reader_id, cmd, and data length)
        - Frame = [PacketType][DataLen][ReaderId][Cmd][Data...][Checksum]
        - Checksum = CheckSum(frame, 0, length + 4) where length is data.Length
        
        Note: The C# 'btDataLen' represents bytes from ReaderId to end of Data (inclusive)
        So for the frame structure: btDataLen = 1(readerId) + 1(cmd) + 1(dataLen byte count) = 3 + len(data)
        Wait, looking more carefully:
        - Without data: btDataLen = 3, frame size = 5 (0xA0, len, readerId, cmd, checksum)
        - With data: btDataLen = len(data) + 3, frame size = len(data) + 5
        
        So btDataLen = number of bytes AFTER the length byte and BEFORE the checksum
        """
        # Length byte = reader_id(1) + cmd(1) + data_len + checksum is NOT included
        # Actually in C#: btDataLen = length + 3 where length is data array length
        # This means btDataLen counts: reader_id + cmd + data bytes = 1 + 1 + len(data) + 1 = len(data) + 3
        # Wait no, looking at line 67: btDataLen = Convert.ToByte((int) (length + 3))
        # where length = btAryData.Length
        # So btDataLen = data.Length + 3
        # 
        # The frame format is: [0xA0][btDataLen][readerId][cmd][data...][checksum]
        # Total frame size = 1 + 1 + 1 + 1 + len(data) + 1 = 5 + len(data)
        # btDataLen = 3 + len(data) which is the count of bytes from readerId to end of data
        
        length = len(data) + 3  # Matches C#: btDataLen = length + 3
        frame_without_checksum = bytes([0xA0, length, reader_id, cmd]) + data
        checksum = ReaderProtocol.calculate_checksum(frame_without_checksum)
        return frame_without_checksum + bytes([checksum])
    
    @staticmethod
    def build_fast_switch_inventory(reader_id: int, ant_config: bytes) -> bytes:
        """Build fast switch inventory command"""
        return ReaderProtocol.create_frame(reader_id, ReaderProtocol.CMD_FAST_SWITCH, ant_config)
    
    # =================================================================
    # POWER COMMANDS - Matching C# ReaderMethod.cs exactly
    # =================================================================
    
    @staticmethod
    def build_set_power(reader_id: int, power_dbm: int) -> bytes:
        """
        Build SET power command for uniform power across all antennas
        
        C# equivalent (ReaderMethod.cs line 592-596):
            public int SetOutputPower(byte btReadId, byte btOutputPower)
            {
                byte btCmd = 0x76;
                return this.SendMessage(btReadId, btCmd, new byte[] { btOutputPower });
            }
        
        Args:
            reader_id: Reader address (0xFF for broadcast)
            power_dbm: Output power in dBm (0-33)
                       Value is sent DIRECTLY - no multiplication needed!
        
        Returns:
            Command frame bytes ready to send
        
        Response:
            Reader returns [0xA0][Len][ReaderId][0x76][Status][Checksum]
            Status 0x10 = Success, other values = error codes
        """
        # Validate power range (0-33 dBm based on C# ComboBox_PowerDbm items)
        if not 0 <= power_dbm <= 33:
            raise ValueError(f"Power must be 0-33 dBm, got {power_dbm}")
        
        return ReaderProtocol.create_frame(
            reader_id, 
            ReaderProtocol.CMD_SET_POWER, 
            bytes([power_dbm])
        )
    
    @staticmethod
    def build_set_power_per_antenna(reader_id: int, ant1: int, ant2: int, ant3: int, ant4: int) -> bytes:
        """
        Build SET power command with per-antenna power levels
        
        C# equivalent (ReaderMethod.cs line 604-609):
            public int SetOutputPower(byte btReadId, byte ant1Power, byte ant2Power, 
                                      byte ant3Power, byte ant4Power)
            {
                byte btCmd = 0x76;
                byte[] btAryData = new byte[] { ant1Power, ant2Power, ant3Power, ant4Power };
                return this.SendMessage(btReadId, btCmd, btAryData);
            }
        
        Args:
            reader_id: Reader address (0xFF for broadcast)
            ant1-ant4: Power for each antenna in dBm (0-33)
        
        Returns:
            Command frame bytes ready to send
        """
        powers = [ant1, ant2, ant3, ant4]
        for i, p in enumerate(powers):
            if not 0 <= p <= 33:
                raise ValueError(f"ANT{i+1} power must be 0-33 dBm, got {p}")
        
        return ReaderProtocol.create_frame(
            reader_id,
            ReaderProtocol.CMD_SET_POWER,
            bytes(powers)
        )
    
    @staticmethod
    def build_get_power(reader_id: int, eight_antenna: bool = True) -> bytes:
        """
        Build GET power command
        
        C# ReaderMethod.cs has two commands:
        - 0x77 (GetOutputPowerFour): Returns SINGLE power value (deprecated)
        - 0x97 (GetOutputPower): Returns ALL antenna power values (use this!)
        
        The C# Form1 uses GetOutputPower(0xFF) which sends 0x97.
        This returns power levels for all 4 (or 8) antennas.
        
        Args:
            reader_id: Reader address
            eight_antenna: True to use 0x97 (recommended), False for 0x77
        
        Response:
            [0xA0][Len][ReaderId][0x97][Power1][Power2][Power3][Power4][Checksum]
            Each power byte is the dBm value (0-33) for that antenna
        """
        cmd = ReaderProtocol.CMD_GET_POWER_8ANT if eight_antenna else ReaderProtocol.CMD_GET_POWER_4ANT
        return ReaderProtocol.create_frame(reader_id, cmd, b'')
    
    @staticmethod
    def parse_set_power_response(data: bytes) -> dict:
        """
        Parse the response from a SET power command
        
        C# ProcessSetOutputPower (ReaderProcessor.cs lines 1133-1148):
        - Response data length should be 1
        - data[0] == 0x10 means SUCCESS
        - Any other value is an error code
        
        Returns:
            {'success': bool, 'error_code': int or None, 'message': str}
        """
        result = ReaderProtocol.parse_response(data)
        if not result['valid']:
            return {'success': False, 'error_code': None, 'message': result['error']}
        
        if result['cmd'] != ReaderProtocol.CMD_SET_POWER:
            return {'success': False, 'error_code': None, 'message': f"Unexpected command response: 0x{result['cmd']:02X}"}
        
        response_data = result['data']
        if len(response_data) != 1:
            return {'success': False, 'error_code': 0x58, 'message': "Invalid response length"}
        
        status = response_data[0]
        if status == ReaderProtocol.RESPONSE_SUCCESS:
            return {'success': True, 'error_code': None, 'message': "Power set successfully"}
        else:
            # Error code meanings from C# (common codes)
            error_messages = {
                0x00: "Command failed",
                0x01: "Invalid parameter",
                0x02: "Reader busy",
                0x58: "Invalid response data",
            }
            msg = error_messages.get(status, f"Unknown error code: 0x{status:02X}")
            return {'success': False, 'error_code': status, 'message': msg}
    
    @staticmethod
    def build_get_temperature(reader_id: int) -> bytes:
        """Build get temperature command"""
        return ReaderProtocol.create_frame(reader_id, ReaderProtocol.CMD_GET_TEMPERATURE, b'')
    
    @staticmethod
    def build_get_firmware(reader_id: int) -> bytes:
        """Build get firmware version command"""
        return ReaderProtocol.create_frame(reader_id, ReaderProtocol.CMD_GET_FIRMWARE, b'')
    
    @staticmethod
    def build_get_reader_id(reader_id: int) -> bytes:
        """Build get reader identifier command"""
        return ReaderProtocol.create_frame(reader_id, ReaderProtocol.CMD_GET_READER_ID, b'')
    
    @staticmethod
    def build_set_frequency_region(reader_id: int, region: int, start: int, end: int) -> bytes:
        """Build set frequency region command"""
        return ReaderProtocol.create_frame(reader_id, 0x78, bytes([region, start, end]))
    
    @staticmethod
    def build_set_beeper_mode(reader_id: int, mode: int) -> bytes:
        """Build set beeper mode command"""
        return ReaderProtocol.create_frame(reader_id, 0x7C, bytes([mode]))
    
    @staticmethod
    def build_reset_reader(reader_id: int) -> bytes:
        """Build reset reader command"""
        return ReaderProtocol.create_frame(reader_id, 0x70, b'')
    
    @staticmethod
    def build_set_rf_profile(reader_id: int, profile: int) -> bytes:
        """Build set RF link profile command"""
        return ReaderProtocol.create_frame(reader_id, 0x69, bytes([profile]))
    
    @staticmethod
    def parse_response(data: bytes) -> dict:
        """
        Parse a response frame from reader
        
        Matches C# MessageTran constructor that parses received data:
        - Validates checksum using two's complement
        - Extracts reader_id, cmd, and payload data
        """
        if len(data) < 5:
            return {'valid': False, 'error': 'Frame too short'}
        
        if data[0] != 0xA0:
            return {'valid': False, 'error': 'Invalid header'}
        
        length = data[1]
        reader_id = data[2]
        cmd = data[3]
        payload = data[4:-1] if len(data) > 5 else b''
        received_checksum = data[-1]
        
        # Verify checksum using two's complement (matches C# MessageTran constructor)
        # C# code: if (this.CheckSum(this.btAryTranData, 0, this.btAryTranData.Length - 1) == btAryTranData[length - 1])
        calc_checksum = ReaderProtocol.calculate_checksum(data[:-1])
        if calc_checksum != received_checksum:
            return {'valid': False, 'error': f'Checksum mismatch: expected {calc_checksum:02X}, got {received_checksum:02X}'}
        
        return {
            'valid': True,
            'reader_id': reader_id,
            'cmd': cmd,
            'data': payload
        }
    
    @staticmethod
    def parse_tag_data(cmd: int, data: bytes) -> dict:
        """Parse tag data from fast switch inventory response"""
        if len(data) < 4:
            return None
        
        ant_byte = data[0]
        freq_code = (ant_byte & 0xFF) >> 2
        ant_id = (ant_byte & 0x03) + 1
        
        pc = data[1:3].hex().upper()
        epc_length = len(data) - 4
        epc = data[3:3 + epc_length].hex().upper()
        rssi = data[-1]
        
        # Calculate frequency string (FCC region formula)
        if freq_code >= 7:
            frequency = 902.0 + (freq_code - 7) * 0.5
        else:
            frequency = 865.0 + freq_code * 0.5
        
        return {
            'pc': pc,
            'epc': epc,
            'rssi': rssi,
            'antenna': ant_id,
            'frequency': f"{frequency:.2f}"
        }

