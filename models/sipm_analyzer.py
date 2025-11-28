"""
SiPM characterization: Crosstalk and Afterpulse analysis.
"""
import numpy as np
from dataclasses import dataclass


@dataclass
class SiPMMetrics:
    """Container for SiPM characterization metrics."""
    # Percentages
    crosstalk_pct: float = 0.0
    afterpulse_pct: float = 0.0
    crosstalk_afterpulse_pct: float = 0.0
    
    # DCR rates (two calculation methods)
    dcr_rate_total_hz: float = 0.0  # Method 1: count / total_time
    dcr_rate_avg_hz: float = 0.0    # Method 2: 1 / mean_interval
    
    # Event counts
    total_events: int = 0
    crosstalk_count: int = 0
    afterpulse_count: int = 0
    crosstalk_afterpulse_count: int = 0
    dcr_count: int = 0
    
    # Thresholds used
    amplitude_threshold: float = 0.0
    time_threshold: float = 0.0
    
    # Masks for visualization
    dcr_mask: np.ndarray = None
    crosstalk_mask: np.ndarray = None
    afterpulse_mask: np.ndarray = None
    crosstalk_afterpulse_mask: np.ndarray = None


class SiPMAnalyzer:
    """Analyze SiPM characteristics from temporal distribution."""
    
    def __init__(self, amplitude_threshold_mV: float = 60.0, 
                 time_threshold_s: float = 1e-4):
        """
        Initialize analyzer with thresholds.
        
        Args:
            amplitude_threshold_mV: Amplitude threshold in mV (horizontal line)
            time_threshold_s: Time threshold in seconds (vertical line)
        """
        self.amp_threshold = amplitude_threshold_mV
        self.time_threshold = time_threshold_s
    
    def analyze(self, delta_t: np.ndarray, amplitudes_mV: np.ndarray) -> SiPMMetrics:
        """
        Analyze SiPM characteristics using threshold-based quadrant classification.
        
        Quadrants:
        - Bottom-Right (long time, low amp): DCR
        - Bottom-Left (short time, low amp): Afterpulses (AP)
        - Top-Right (long time, high amp): Crosstalk (XT)
        - Top-Left (short time, high amp): Afterpulse + Crosstalk (AP+XT)
        
        Args:
            delta_t: Time differences between consecutive peaks (s)
            amplitudes_mV: Peak amplitudes (mV)
            
        Returns:
            SiPMMetrics with calculated percentages
        """
        metrics = SiPMMetrics()
        metrics.amplitude_threshold = self.amp_threshold
        metrics.time_threshold = self.time_threshold
        
        total_events = len(delta_t)
        metrics.total_events = total_events
        
        if total_events == 0:
            return metrics
        
        # Classify events into quadrants
        # Bottom-Right: DCR (long time, low amplitude)
        dcr_mask = (delta_t >= self.time_threshold) & (amplitudes_mV < self.amp_threshold)
        
        # Bottom-Left: Afterpulses (short time, low amplitude)
        ap_mask = (delta_t < self.time_threshold) & (amplitudes_mV < self.amp_threshold)
        
        # Top-Right: Crosstalk (long time, high amplitude)
        xt_mask = (delta_t >= self.time_threshold) & (amplitudes_mV >= self.amp_threshold)
        
        # Top-Left: Afterpulse + Crosstalk (short time, high amplitude)
        ap_xt_mask = (delta_t < self.time_threshold) & (amplitudes_mV >= self.amp_threshold)
        
        # Store masks
        metrics.dcr_mask = dcr_mask
        metrics.afterpulse_mask = ap_mask
        metrics.crosstalk_mask = xt_mask
        metrics.crosstalk_afterpulse_mask = ap_xt_mask
        
        # Count events
        metrics.dcr_count = np.sum(dcr_mask)
        metrics.afterpulse_count = np.sum(ap_mask)
        metrics.crosstalk_count = np.sum(xt_mask)
        metrics.crosstalk_afterpulse_count = np.sum(ap_xt_mask)
        
        # Calculate percentages (over total events)
        metrics.afterpulse_pct = (metrics.afterpulse_count / total_events) * 100
        metrics.crosstalk_pct = (metrics.crosstalk_count / total_events) * 100
        metrics.crosstalk_afterpulse_pct = (metrics.crosstalk_afterpulse_count / total_events) * 100
        
        # Calculate DCR (Dark Count Rate) using two methods
        if metrics.dcr_count > 0:
            dcr_intervals = delta_t[dcr_mask]
            
            # Method 1: Total rate = events / total_time
            # This gives the overall average rate across all DCR intervals
            total_time_dcr = np.sum(dcr_intervals)
            if total_time_dcr > 0:
                metrics.dcr_rate_total_hz = metrics.dcr_count / total_time_dcr
            
            # Method 2: Average rate = 1 / mean_interval
            # This gives the rate based on the typical interval between events
            mean_interval_dcr = np.mean(dcr_intervals)
            if mean_interval_dcr > 0:
                metrics.dcr_rate_avg_hz = 1.0 / mean_interval_dcr
        
        return metrics
