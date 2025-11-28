"""
Analysis controller - orchestrates the analysis workflow.
"""
from models.waveform_data import WaveformData
from models.peak_analyzer import PeakAnalyzer
from models.analysis_results import AnalysisResults


class AnalysisController:
    """Coordinates analysis between model and view."""
    
    def __init__(self):
        """Initialize the analysis controller."""
        self.waveform_data = WaveformData()
        self.peak_analyzer = PeakAnalyzer(self.waveform_data)
        self.results = AnalysisResults()
        
        # Current navigation indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_rejected_afterpulse_idx = 0
    
    def load_data(self) -> int:
        """
        Load waveform data from configured directory.
        
        Returns:
            Number of files loaded
        """
        return self.waveform_data.load_files()
    
    def run_analysis(
        self,
        prominence_pct: float,
        width_time: float,
        min_dist_time: float,
        baseline_pct: float,
        max_dist_pct: float,
        afterpulse_pct: float
    ) -> AnalysisResults:
        """
        Run peak analysis with given parameters.
        
        Args:
            prominence_pct: Prominence as percentage
            width_time: Minimum width in seconds
            min_dist_time: Minimum distance in seconds
            baseline_pct: Baseline percentile
            max_dist_pct: Max distance percentile
            afterpulse_pct: Afterpulse percentile
            
        Returns:
            Analysis results
        """
        self.results = self.peak_analyzer.analyze_all(
            prominence_pct,
            width_time,
            min_dist_time,
            baseline_pct,
            max_dist_pct,
            afterpulse_pct
        )
        
        # Reset navigation indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_rejected_afterpulse_idx = 0
        
        return self.results
    
    def navigate_next(self, category: str) -> bool:
        """
        Navigate to next item in category.
        
        Args:
            category: One of 'accepted', 'rejected', 'afterpulse', 'rejected_afterpulse'
            
        Returns:
            True if navigation successful, False if at end
        """
        if category == "accepted":
            if self.current_accepted_idx < len(self.results.accepted_results) - 1:
                self.current_accepted_idx += 1
                return True
        elif category == "rejected":
            if self.current_rejected_idx < len(self.results.rejected_results) - 1:
                self.current_rejected_idx += 1
                return True
        elif category == "afterpulse":
            if self.current_afterpulse_idx < len(self.results.afterpulse_results) - 1:
                self.current_afterpulse_idx += 1
                return True
        elif category == "rejected_afterpulse":
            if self.current_rejected_afterpulse_idx < len(self.results.rejected_afterpulse_results) - 1:
                self.current_rejected_afterpulse_idx += 1
                return True
        return False
    
    def navigate_prev(self, category: str) -> bool:
        """
        Navigate to previous item in category.
        
        Args:
            category: One of 'accepted', 'rejected', 'afterpulse', 'rejected_afterpulse'
            
        Returns:
            True if navigation successful, False if at beginning
        """
        if category == "accepted":
            if self.current_accepted_idx > 0:
                self.current_accepted_idx -= 1
                return True
        elif category == "rejected":
            if self.current_rejected_idx > 0:
                self.current_rejected_idx -= 1
                return True
        elif category == "afterpulse":
            if self.current_afterpulse_idx > 0:
                self.current_afterpulse_idx -= 1
                return True
        elif category == "rejected_afterpulse":
            if self.current_rejected_afterpulse_idx > 0:
                self.current_rejected_afterpulse_idx -= 1
                return True
        return False
    
    def get_current_index(self, category: str) -> int:
        """Get current navigation index for category."""
        if category == "accepted":
            return self.current_accepted_idx
        elif category == "rejected":
            return self.current_rejected_idx
        elif category == "afterpulse":
            return self.current_afterpulse_idx
        elif category == "rejected_afterpulse":
            return self.current_rejected_afterpulse_idx
        return 0
    
    def get_results_for_category(self, category: str) -> list:
        """Get results list for a specific category."""
        if category == "accepted":
            return self.results.accepted_results
        elif category == "rejected":
            return self.results.rejected_results
        elif category == "afterpulse":
            return self.results.afterpulse_results
        elif category == "rejected_afterpulse":
            return self.results.rejected_afterpulse_results
        return []
