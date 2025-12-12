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
    peak_rejection_reasons: Dict[int, str] = field(default_factory=dict)  # Maps peak index to rejection reason


@dataclass
class AnalysisResults:
    """Container for all analysis results."""
    accepted_results: List[WaveformResult] = field(default_factory=list)
    rejected_results: List[WaveformResult] = field(default_factory=list)
    afterpulse_results: List[WaveformResult] = field(default_factory=list)
    favorites_results: List[WaveformResult] = field(default_factory=list)
    
    # Statistics
    total_peaks: int = 0
    baseline_low: float = 0.0
    baseline_high: float = 0.0
    max_dist_low: float = 0.0
    max_dist_high: float = 0.0
    # Note: afterpulse_low/high removed - zone calculation no longer used
    
    def __post_init__(self):
        """Ensure favorites_results exists for backward compatibility."""
        if not hasattr(self, 'favorites_results'):
            self.favorites_results = []
    
    def get_accepted_count(self) -> int:
        """Get number of accepted waveforms."""
        return len(self.accepted_results)
    
    def get_rejected_count(self) -> int:
        """Get number of rejected waveforms."""
        return len(self.rejected_results)
    
    def get_afterpulse_count(self) -> int:
        """Get number of afterpulse waveforms."""
        return len(self.afterpulse_results)
    
    def get_favorites_count(self) -> int:
        """Get number of favorite waveforms."""
        return len(self.favorites_results)
    
    def add_to_favorites(self, result: WaveformResult):
        """Add a waveform to favorites."""
        # Check if already in favorites
        if not any(f.filename == result.filename for f in self.favorites_results):
            self.favorites_results.append(result)
    
    def remove_from_favorites(self, filename: str):
        """Remove a waveform from favorites by filename."""
        self.favorites_results = [f for f in self.favorites_results if f.filename != filename]
    
    def is_favorite(self, filename: str) -> bool:
        """Check if a waveform is in favorites."""
        return any(f.filename == filename for f in self.favorites_results)
    
    def get_favorite_original_category(self, filename: str) -> str:
        """Get the original category of a favorite (accepted/rejected/afterpulse)."""
        # Check in accepted
        if any(r.filename == filename for r in self.accepted_results):
            return "accepted"
        # Check in afterpulse
        elif any(r.filename == filename for r in self.afterpulse_results):
            return "afterpulse"
        # Check in rejected
        elif any(r.filename == filename for r in self.rejected_results):
            return "rejected"
        return "unknown"
    
    def clear(self):
        """Clear all results."""
        self.accepted_results.clear()
        self.rejected_results.clear()
        self.afterpulse_results.clear()
        self.favorites_results.clear()
        self.total_peaks = 0
