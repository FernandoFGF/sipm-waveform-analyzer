"""
Analysis controller - orchestrates the analysis workflow.
"""
from models.waveform_data import WaveformData
from models.peak_analyzer import PeakAnalyzer
from models.analysis_results import AnalysisResults, WaveformResult
from models.results_cache import ResultsCache
from models.favorites_manager import FavoritesManager
import config


class AnalysisController:
    """Coordinates analysis between model and view."""
    
    def __init__(self, data_dir=None):
        """Initialize the analysis controller.
        
        Args:
            data_dir: Data directory path. If None, uses config.DATA_DIR
        """
        if data_dir is None:
            data_dir = config.DATA_DIR
        
        self.waveform_data = WaveformData(data_dir)
        self.peak_analyzer = PeakAnalyzer(self.waveform_data)
        self.results = AnalysisResults()
        self.cache = ResultsCache()  # Initialize cache
        self.favorites_manager = FavoritesManager(data_dir)  # Initialize favorites manager
        
        # Current navigation indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_favorites_idx = 0
    
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
        negative_trigger_mv: float
    ) -> AnalysisResults:
        """
        Run peak analysis with given parameters.
        
        Args:
            prominence_pct: Prominence as percentage
            width_time: Minimum width in seconds
            min_dist_time: Minimum distance in seconds
            baseline_pct: Baseline percentile
            max_dist_pct: Max distance percentile
            negative_trigger_mv: Negative trigger threshold in mV
            
        Returns:
            Analysis results
        """
        # Prepare parameters for caching
        params = {
            'prominence_pct': prominence_pct,
            'width_time': width_time,
            'min_dist_time': min_dist_time,
            'baseline_pct': baseline_pct,
            'max_dist_pct': max_dist_pct,
            'negative_trigger_mv': negative_trigger_mv
        }
        
        # Generate cache key including DATA_DIR to differentiate datasets
        cache_key = self.cache.get_cache_key(
            self.waveform_data.waveform_files,
            params,
            data_dir=str(config.DATA_DIR)
        )
        
        # Try to load from cache
        cached_results = self.cache.load(cache_key)
        
        if cached_results is not None:
            print("Using cached results (instant!)")
            self.results = cached_results
        else:
            # Run analysis
            print("Running new analysis...")
            self.results = self.peak_analyzer.analyze_all(
                prominence_pct,
                width_time,
                min_dist_time,
                baseline_pct,
                max_dist_pct,
                negative_trigger_mv
            )
            
            # Save to cache
            self.cache.save(cache_key, self.results, params)
        
        # Reset navigation indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_favorites_idx = 0
        
        # Populate favorites from saved list
        self.populate_favorites_from_saved()
        
        return self.results
    
    def navigate_next(self, category: str) -> bool:
        """
        Navigate to next item in category.
        
        Args:
            category: One of 'accepted', 'rejected', 'afterpulse', 'favorites'
            
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
        elif category == "favorites":
            if self.current_favorites_idx < len(self.results.favorites_results) - 1:
                self.current_favorites_idx += 1
                return True
        return False
    
    def navigate_prev(self, category: str) -> bool:
        """
        Navigate to previous item in category.
        
        Args:
            category: One of 'accepted', 'rejected', 'afterpulse', 'favorites'
            
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
        elif category == "favorites":
            if self.current_favorites_idx > 0:
                self.current_favorites_idx -= 1
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
        elif category == "favorites":
            return self.current_favorites_idx
        return 0
    
    def get_results_for_category(self, category: str) -> list:
        """Get results list for a specific category."""
        if category == "accepted":
            return self.results.accepted_results
        elif category == "rejected":
            return self.results.rejected_results
        elif category == "afterpulse":
            return self.results.afterpulse_results
        elif category == "favorites":
            return self.results.favorites_results
        return []
    
    def add_to_favorites(self, result: WaveformResult):
        """Add a waveform to favorites."""
        self.favorites_manager.add_favorite(result.filename)
        self.results.add_to_favorites(result)
    
    def remove_from_favorites(self, filename: str):
        """Remove a waveform from favorites."""
        self.favorites_manager.remove_favorite(filename)
        self.results.remove_from_favorites(filename)
        
        # Adjust current index if it's now out of bounds
        if self.current_favorites_idx >= len(self.results.favorites_results):
            self.current_favorites_idx = max(0, len(self.results.favorites_results) - 1)
    
    def is_favorite(self, filename: str) -> bool:
        """Check if a waveform is in favorites."""
        return self.favorites_manager.is_favorite(filename)
    
    def populate_favorites_from_saved(self):
        """Populate favorites results from saved favorites list."""
        saved_favorites = self.favorites_manager.get_favorites()
        
        # Search for each saved favorite in all result categories
        all_results = (
            self.results.accepted_results +
            self.results.rejected_results +
            self.results.afterpulse_results
        )
        
        for result in all_results:
            if result.filename in saved_favorites:
                self.results.add_to_favorites(result)
