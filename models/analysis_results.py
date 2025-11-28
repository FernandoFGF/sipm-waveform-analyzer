"""
Data structures for analysis results.
"""
from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np
from pathlib import Path


@dataclass
class WaveformResult:
    """Result for a single waveform analysis."""
    filename: str
    t_half: float
    amplitudes: np.ndarray
    peaks: np.ndarray  # Valid peaks that passed all filters
    all_peaks: np.ndarray  # All peaks initially detected
    properties: Dict  # scipy find_peaks properties


@dataclass
class AnalysisResults:
    """Container for all analysis results."""
    accepted_results: List[WaveformResult] = field(default_factory=list)
    rejected_results: List[WaveformResult] = field(default_factory=list)
    afterpulse_results: List[WaveformResult] = field(default_factory=list)
    rejected_afterpulse_results: List[WaveformResult] = field(default_factory=list)
    
    # Statistics
    total_peaks: int = 0
    baseline_low: float = 0.0
    baseline_high: float = 0.0
    max_dist_low: float = 0.0
    max_dist_high: float = 0.0
    afterpulse_low: float = 0.0
    afterpulse_high: float = 0.0
    
    def get_accepted_count(self) -> int:
        """Get number of accepted waveforms."""
        return len(self.accepted_results)
    
    def get_rejected_count(self) -> int:
        """Get number of rejected waveforms."""
        return len(self.rejected_results)
    
    def get_afterpulse_count(self) -> int:
        """Get number of afterpulse waveforms."""
        return len(self.afterpulse_results)
    
    def get_rejected_afterpulse_count(self) -> int:
        """Get number of rejected afterpulse waveforms."""
        return len(self.rejected_afterpulse_results)
    
    def clear(self):
        """Clear all results."""
        self.accepted_results.clear()
        self.rejected_results.clear()
        self.afterpulse_results.clear()
        self.rejected_afterpulse_results.clear()
        self.total_peaks = 0
