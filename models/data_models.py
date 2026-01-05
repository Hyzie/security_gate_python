"""
Data Models for RFID Reader Application
Defines core data structures used throughout the application
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List, Dict
import threading


class SensorDirection(Enum):
    """Direction detected by dual-sensor system"""
    UNKNOWN = auto()
    IN = auto()   # S2 activates before S1
    OUT = auto()  # S1 activates before S2


@dataclass
class EPCReadEvent:
    """Represents a single RFID tag read event"""
    epc: str
    rssi: int
    read_time: datetime
    antenna: int
    frequency: str = ""
    pc: str = ""
    
    def __post_init__(self):
        if self.read_time is None:
            self.read_time = datetime.now()


@dataclass
class RXInventoryTag:
    """Inventory tag data received from reader"""
    str_pc: str = ""
    str_epc: str = ""
    str_rssi: str = ""
    str_freq: str = ""
    bt_ant_id: int = 0
    cmd: int = 0


@dataclass 
class SensorState:
    """Manages sensor state for direction detection"""
    s1_activated_time: Optional[datetime] = None
    s2_activated_time: Optional[datetime] = None
    s1_was_active: bool = False
    s2_was_active: bool = False
    last_direction: SensorDirection = SensorDirection.UNKNOWN
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    
    @property
    def both_sensors_activated(self) -> bool:
        """Check if both sensors have been activated"""
        return self.s1_activated_time is not None and self.s2_activated_time is not None
    
    def get_direction(self) -> SensorDirection:
        """Determine direction based on sensor activation order"""
        if not self.both_sensors_activated:
            return SensorDirection.UNKNOWN
        return SensorDirection.OUT if self.s1_activated_time < self.s2_activated_time else SensorDirection.IN
    
    def get_time_difference_ms(self) -> float:
        """Get time difference between sensor activations in milliseconds"""
        if not self.both_sensors_activated:
            return 0.0
        return abs((self.s2_activated_time - self.s1_activated_time).total_seconds() * 1000)
    
    def get_trigger_time(self) -> datetime:
        """Get the trigger time (whichever sensor activated last)"""
        if not self.both_sensors_activated:
            return datetime.now()
        return max(self.s1_activated_time, self.s2_activated_time)
    
    def reset(self):
        """Reset sensor state"""
        self.s1_activated_time = None
        self.s2_activated_time = None
        self.last_direction = SensorDirection.UNKNOWN


@dataclass
class ReaderSettings:
    """Reader configuration settings"""
    # Reader identification
    bt_read_id: int = 0xFF
    bt_reader_identifier: str = ""
    
    # Firmware info
    bt_major: int = 0
    bt_minor: int = 0
    
    # Antenna settings
    bt_work_antenna: int = 0
    
    # Power settings (per antenna)
    bt_output_power: int = 0
    bt_output_powers: Optional[List[int]] = None
    
    # Frequency region
    bt_region: int = 0
    bt_frequency_start: int = 0
    bt_frequency_end: int = 0
    bt_user_define_frequency_interval: int = 0
    bt_user_define_channel_quantity: int = 0
    n_user_define_start_frequency: int = 0
    
    # Temperature
    bt_plus_minus: int = 0
    bt_temperature: int = 0
    
    # RF settings
    bt_link_profile: int = 0
    bt_ant_impedance: int = 0
    
    # GPIO
    bt_gpio1_value: int = 0
    bt_gpio2_value: int = 0
    bt_gpio3_value: int = 0
    bt_gpio4_value: int = 0
    
    # Monza
    bt_monza_status: int = 0
    
    def get_temperature_string(self) -> str:
        """Get formatted temperature string"""
        sign = "" if self.bt_plus_minus != 0 else "-"
        return f"{sign}{self.bt_temperature}°C"
    
    def get_firmware_version(self) -> str:
        """Get formatted firmware version"""
        return f"{self.bt_major}.{self.bt_minor}"


class FrequencyRegion(Enum):
    """Supported frequency regions"""
    US = (0x01, 0x07, 0x3B, "US (902-928 MHz)")
    CHINA = (0x01, 0x2B, 0x35, "China (920-925 MHz)")
    VIETNAM = (0x01, 0x27, 0x31, "Vietnam (918-923 MHz)")
    EUROPE = (0x02, 0x00, 0x06, "Europe (865-868 MHz)")
    
    def __init__(self, region_code, start, end, description):
        self.region_code = region_code
        self.start_freq = start
        self.end_freq = end
        self.description = description


class RFLinkProfile(Enum):
    """RF Link profiles"""
    PROFILE_0 = (0xD0, "Tari 25μs, FM0, LF=40KHz")
    PROFILE_1 = (0xD1, "Tari 25μs, Miller 4, LF=250KHz")
    PROFILE_2 = (0xD2, "Tari 25μs, Miller 4, LF=300KHz")
    PROFILE_3 = (0xD3, "Tari 6.25μs, FM0, LF=400KHz")
    
    def __init__(self, code, description):
        self.code = code
        self.description = description


class SessionTarget:
    """Session and Target settings for inventory"""
    SESSIONS = {
        'S0': (0x00, 50),   # (code, typical loop time ms)
        'S1': (0x01, 200),
        'S2': (0x02, 300),
        'S3': (0x03, 500),
    }
    
    TARGETS = {
        'A': 0x00,
        'B': 0x01,
    }

