"""
Reader Model - Business Logic for RFID Reader
Handles tag processing, analysis, and data management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Tuple
import threading
import statistics

from .data_models import (
    EPCReadEvent, SensorState, SensorDirection, 
    ReaderSettings, RXInventoryTag
)


@dataclass
class AnalysisResult:
    """Result of tag analysis with confidence scores"""
    epc: str
    confidence_ant1: float
    confidence_ant2: float
    confidence_all: float
    direction: SensorDirection


class ReaderModel:
    """
    Core business logic for RFID reader operations
    Manages tag inventory, analysis, and sensor integration
    """
    
    # Analysis constants
    CONFIDENCE_THRESHOLD = 30.0
    ALPHA = 0.5
    SLOPE_MIN_THRESHOLD = 0.5
    SLOPE_MAX_THRESHOLD = 15.0
    VARIANCE_MIN_THRESHOLD = 2.0
    VARIANCE_MAX_THRESHOLD = 40.0
    MAX_TOTAL_TAGS = 10000
    
    def __init__(self):
        self._epc_dictionary: Dict[str, int] = {}
        self._epc_read_history: List[EPCReadEvent] = []
        self._history_lock = threading.Lock()
        
        self._sensor_state = SensorState()
        self._sensor_lock = threading.Lock()
        
        self._settings = ReaderSettings()
        self._total_tag_count = 0
        self._detected_direction = SensorDirection.X
        
        # Sensor activation times for export
        self._last_s1_activation: Optional[datetime] = None
        self._last_s2_activation: Optional[datetime] = None
        self._sensor_activated_time: Optional[datetime] = None
        
        # Callbacks
        self._on_tag_detected: Optional[Callable[[RXInventoryTag], None]] = None
        self._on_sensor_triggered: Optional[Callable[[SensorDirection, float], None]] = None
        self._on_log: Optional[Callable[[str], None]] = None
    
    @property
    def epc_count(self) -> int:
        """Get unique EPC count"""
        return len(self._epc_dictionary)
    
    @property
    def total_tag_count(self) -> int:
        """Get total tag read count"""
        return self._total_tag_count
    
    @property
    def settings(self) -> ReaderSettings:
        """Get reader settings"""
        return self._settings
    
    @property
    def detected_direction(self) -> SensorDirection:
        """Get last detected direction"""
        return self._detected_direction
    
    def set_callbacks(self, 
                      on_tag: Callable[[RXInventoryTag], None] = None,
                      on_sensor: Callable[[SensorDirection, float], None] = None,
                      on_log: Callable[[str], None] = None):
        """Set callback functions"""
        self._on_tag_detected = on_tag
        self._on_sensor_triggered = on_sensor
        self._on_log = on_log
    
    def _log(self, message: str):
        """Log a message through callback"""
        if self._on_log:
            self._on_log(message)
    
    def clear_data(self):
        """Clear all inventory data"""
        with self._history_lock:
            self._epc_dictionary.clear()
            self._epc_read_history.clear()
        self._total_tag_count = 0
        self._detected_direction = SensorDirection.X
    
    def process_tag(self, tag: RXInventoryTag) -> bool:
        """
        Process an incoming tag read
        Returns True if this is a new unique tag
        """
        if not tag.str_epc or tag.str_epc in ("000000", "000001"):
            return False
        
        self._total_tag_count += 1
        
        # Check for max tags
        if self._total_tag_count >= self.MAX_TOTAL_TAGS:
            self.clear_data()
        
        is_new = tag.str_epc not in self._epc_dictionary
        
        if is_new:
            self._epc_dictionary[tag.str_epc] = 1
        else:
            self._epc_dictionary[tag.str_epc] += 1
        
        # Record in history
        event = EPCReadEvent(
            epc=tag.str_epc,
            rssi=int(tag.str_rssi) if tag.str_rssi else 0,
            read_time=datetime.now(),
            antenna=tag.bt_ant_id,
            frequency=tag.str_freq,
            pc=tag.str_pc
        )
        
        with self._history_lock:
            self._epc_read_history.append(event)
        
        if self._on_tag_detected:
            self._on_tag_detected(tag)
        
        return is_new
    
    def get_tag_count(self, epc: str) -> int:
        """Get read count for a specific EPC"""
        return self._epc_dictionary.get(epc, 0)
    
    def get_all_tags(self) -> Dict[str, int]:
        """Get dictionary of all EPCs with their counts"""
        return dict(self._epc_dictionary)
    
    def handle_sensor_activation(self, is_sensor1: bool, activation_time: datetime) -> bool:
        """
        Handle sensor activation event
        Returns True if both sensors triggered (direction determined)
        """
        should_trigger = False
        direction = SensorDirection.X
        time_diff = 0.0
        
        with self._sensor_lock:
            if is_sensor1:
                self._sensor_state.s1_activated_time = activation_time
                self._log(f"S1 activated at {activation_time.strftime('%H:%M:%S.%f')[:-3]}")
            else:
                self._sensor_state.s2_activated_time = activation_time
                self._log(f"S2 activated at {activation_time.strftime('%H:%M:%S.%f')[:-3]}")
            
            if self._sensor_state.both_sensors_activated:
                # Save times for export
                self._last_s1_activation = self._sensor_state.s1_activated_time
                self._last_s2_activation = self._sensor_state.s2_activated_time
                
                direction = self._sensor_state.get_direction()
                time_diff = self._sensor_state.get_time_difference_ms()
                trigger_time = self._sensor_state.get_trigger_time()
                
                self._sensor_state.last_direction = direction
                self._detected_direction = direction
                self._sensor_activated_time = trigger_time
                self._sensor_state.reset()
                should_trigger = True
        
        if should_trigger:
            self._log(f"Direction: {direction.name} | Time diff: {time_diff:.1f}ms")
            if self._on_sensor_triggered:
                self._on_sensor_triggered(direction, time_diff)
        
        return should_trigger
    
    def analyze_tags(self) -> List[AnalysisResult]:
        """
        Analyze tags for confidence-based detection
        Uses RSSI slope and variance analysis
        """
        stop_time = datetime.now()
        slope_window_start = stop_time - timedelta(seconds=2)
        ampl_window_start = stop_time - timedelta(seconds=4)
        
        def canon_epc(s: str) -> str:
            if not s:
                return ""
            return ''.join(c for c in s if not c.isspace() and c != '-').upper()
        
        with self._history_lock:
            snapshot = list(self._epc_read_history)
        
        # Filter by time windows
        history_for_slope = [ev for ev in snapshot if slope_window_start <= ev.read_time <= stop_time]
        history_for_ampl = [ev for ev in snapshot if ampl_window_start <= ev.read_time <= stop_time]
        
        # Group by EPC and antenna
        slope_dict: Dict[Tuple[str, int], float] = {}
        variance_dict: Dict[Tuple[str, int], float] = {}
        slope_all_dict: Dict[str, float] = {}
        variance_all_dict: Dict[str, float] = {}
        
        # Calculate slopes per antenna
        slope_groups = self._group_by(history_for_slope, lambda ev: (canon_epc(ev.epc), ev.antenna))
        for key, events in slope_groups.items():
            median_events = self._get_median_rssi_per_second(events)
            if len(median_events) >= 2:
                slope = self._calculate_linear_regression_slope(median_events)
                if slope <= 30:
                    slope_dict[key] = slope
        
        # Calculate slopes for all antennas combined
        slope_all_groups = self._group_by(history_for_slope, lambda ev: canon_epc(ev.epc))
        for epc, events in slope_all_groups.items():
            median_events = self._get_median_rssi_per_second(events)
            if len(median_events) >= 2:
                slope = self._calculate_linear_regression_slope(median_events)
                if slope <= 30:
                    slope_all_dict[epc] = slope
        
        # Calculate variance per antenna
        ampl_groups = self._group_by(history_for_ampl, lambda ev: (canon_epc(ev.epc), ev.antenna))
        for key, events in ampl_groups.items():
            if len(events) >= 2:
                rssi_values = [ev.rssi for ev in events]
                variance_dict[key] = statistics.variance(rssi_values) if len(rssi_values) > 1 else 0
        
        # Calculate variance for all antennas combined
        ampl_all_groups = self._group_by(history_for_ampl, lambda ev: canon_epc(ev.epc))
        for epc, events in ampl_all_groups.items():
            if len(events) >= 2:
                rssi_values = [ev.rssi for ev in events]
                variance_all_dict[epc] = statistics.variance(rssi_values) if len(rssi_values) > 1 else 0
        
        # Collect all EPCs
        all_epcs = set()
        all_epcs.update(k[0] for k in slope_dict.keys())
        all_epcs.update(k[0] for k in variance_dict.keys())
        all_epcs.update(slope_all_dict.keys())
        all_epcs.update(variance_all_dict.keys())
        
        # Calculate confidence and filter
        results = []
        for epc in all_epcs:
            rel1 = self._try_confidence(epc, 1, slope_dict, variance_dict)
            rel2 = self._try_confidence(epc, 2, slope_dict, variance_dict)
            rel_all = self._try_confidence_all(epc, slope_all_dict, variance_all_dict)
            
            # Count how many pass threshold
            threshold_count = sum([
                rel_all > self.CONFIDENCE_THRESHOLD,
                rel1 > self.CONFIDENCE_THRESHOLD,
                rel2 > self.CONFIDENCE_THRESHOLD
            ])
            
            if threshold_count >= 2:
                results.append(AnalysisResult(
                    epc=epc,
                    confidence_ant1=rel1,
                    confidence_ant2=rel2,
                    confidence_all=rel_all,
                    direction=self._detected_direction
                ))
        
        # Sort by confidence
        results.sort(key=lambda r: (r.confidence_all, max(r.confidence_ant1, r.confidence_ant2), r.epc), reverse=True)
        
        return results
    
    def _group_by(self, items: List, key_func) -> Dict:
        """Group items by a key function"""
        groups = {}
        for item in items:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
    
    def _get_median_rssi_per_second(self, events: List[EPCReadEvent]) -> List[EPCReadEvent]:
        """Get median RSSI for each second"""
        # Group by second
        by_second = {}
        for ev in events:
            key = ev.read_time.replace(microsecond=0)
            if key not in by_second:
                by_second[key] = []
            by_second[key].append(ev)
        
        result = []
        for sec, evs in sorted(by_second.items()):
            sorted_evs = sorted(evs, key=lambda e: e.rssi)
            count = len(sorted_evs)
            if count % 2 == 1:
                median_rssi = sorted_evs[count // 2].rssi
            else:
                median_rssi = (sorted_evs[count // 2 - 1].rssi + sorted_evs[count // 2].rssi) // 2
            
            result.append(EPCReadEvent(
                epc=sorted_evs[0].epc,
                rssi=median_rssi,
                read_time=sec,
                antenna=sorted_evs[0].antenna
            ))
        
        return result
    
    def _calculate_linear_regression_slope(self, events: List[EPCReadEvent]) -> float:
        """Calculate linear regression slope of RSSI over time"""
        n = len(events)
        if n < 2:
            return 0.0
        
        t0 = events[0].read_time
        x = [(ev.read_time - t0).total_seconds() for ev in events]
        y = [ev.rssi for ev in events]
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_xx - sum_x * sum_x
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _to_confidence(self, slope: float, variance: float) -> float:
        """Convert slope and variance to confidence score"""
        s_slope = (slope - self.SLOPE_MIN_THRESHOLD) / (self.SLOPE_MAX_THRESHOLD - self.SLOPE_MIN_THRESHOLD)
        s_slope = max(0.0, min(1.0, s_slope))
        
        s_variance = (variance - self.VARIANCE_MIN_THRESHOLD) / (self.VARIANCE_MAX_THRESHOLD - self.VARIANCE_MIN_THRESHOLD)
        s_variance = max(0.0, min(1.0, s_variance))
        
        return (s_slope * (1 - self.ALPHA) + s_variance * self.ALPHA) * 100.0
    
    def _try_confidence(self, epc: str, antenna: int, 
                        slope_dict: Dict, variance_dict: Dict) -> float:
        """Try to calculate confidence for specific antenna"""
        key = (epc, antenna)
        if key in slope_dict and key in variance_dict:
            return self._to_confidence(slope_dict[key], variance_dict[key])
        return 0.0
    
    def _try_confidence_all(self, epc: str, 
                            slope_dict: Dict, variance_dict: Dict) -> float:
        """Try to calculate confidence for all antennas combined"""
        if epc in slope_dict and epc in variance_dict:
            return self._to_confidence(slope_dict[epc], variance_dict[epc])
        return 0.0
    
    def get_history_for_export(self) -> List[Dict]:
        """Get read history formatted for export"""
        with self._history_lock:
            export_data = []
            tolerance_ms = 100
            
            for i, ev in enumerate(self._epc_read_history):
                is_s1 = False
                is_s2 = False
                
                if self._last_s1_activation:
                    delta = abs((ev.read_time - self._last_s1_activation).total_seconds() * 1000)
                    if delta <= tolerance_ms:
                        is_s1 = True
                
                if self._last_s2_activation:
                    delta = abs((ev.read_time - self._last_s2_activation).total_seconds() * 1000)
                    if delta <= tolerance_ms:
                        is_s2 = True
                
                export_data.append({
                    'index': i + 1,
                    'antenna': ev.antenna,
                    'epc': ev.epc,
                    'rssi': ev.rssi,
                    'timestamp': ev.read_time.strftime('%H:%M:%S.%f')[:-3],
                    's1': is_s1,
                    's2': is_s2
                })
            
            return export_data

