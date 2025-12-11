"""
Analysis controller - orchestrates the analysis workflow.
"""
from pathlib import Path
from typing import Dict, Optional, Callable

from models.waveform_data import WaveformData
from models.peak_analyzer import PeakAnalyzer
from models.analysis_results import AnalysisResults, WaveformResult
from utils.results_cache import ResultsCache
from utils.favorites_manager import FavoritesManager
from utils import get_perf_logger, get_config, read_data_config
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
        self.config_manager = get_config()  # Configuration manager
        
        # Current navigation indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_favorites_idx = 0
    
    def load_data(self, progress_callback=None) -> int:
        """
        Load waveform data from configured directory.
        
        Args:
            progress_callback: Optional callback for progress updates
        
        Returns:
            Number of files loaded
        """
        perf_logger = get_perf_logger()
        with perf_logger.measure("Load Waveform Data", {"directory": str(config.DATA_DIR)}):
            return self.waveform_data.load_files(progress_callback=progress_callback)
    
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
        perf_logger = get_perf_logger()
        
        with perf_logger.measure("Run Analysis", {"files": len(self.waveform_data.waveform_files)}):
            # Prepare parameters for caching
            params = {
                'prominence_pct': prominence_pct,
                'width_time': width_time,
                'min_dist_time': min_dist_time,
                'baseline_pct': baseline_pct,
                'max_dist_pct': max_dist_pct,
                'afterpulse_pct': afterpulse_pct
            }
            
            # Generate cache key including DATA_DIR to differentiate datasets
            with perf_logger.measure("Generate Cache Key"):
                cache_key = self.cache.get_cache_key(
                    self.waveform_data.waveform_files,
                    params,
                    data_dir=str(config.DATA_DIR)
                )
            
            # Try to load from cache
            with perf_logger.measure("Check Cache"):
                cached_results = self.cache.load(cache_key)
            
            if cached_results is not None:
                print("Using cached results (instant!)")
                self.results = cached_results
            else:
                # Run analysis
                print("Running new analysis...")
                with perf_logger.measure("Peak Analysis", {"files": len(self.waveform_data.waveform_files)}):
                    self.results = self.peak_analyzer.analyze_all(
                        prominence_pct,
                        width_time,
                        min_dist_time,
                        baseline_pct,
                        max_dist_pct,
                        afterpulse_pct
                    )
                
                # Save to cache
                with perf_logger.measure("Save to Cache"):
                    self.cache.save(cache_key, self.results, params)
            
            # Reset navigation indices
            self.current_accepted_idx = 0
            self.current_rejected_idx = 0
            self.current_afterpulse_idx = 0
            self.current_favorites_idx = 0
            
            # Populate favorites from saved list
            with perf_logger.measure("Populate Favorites"):
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
    
    # ===== Configuration Management =====
    
    def save_configuration(self, params: Dict[str, float]) -> bool:
        """Save analysis parameters to configuration.
        
        Args:
            params: Dictionary of analysis parameters
            
        Returns:
            True if save successful
        """
        try:
            self.config_manager.save_analysis_params(params)
            print("✓ Configuration saved!")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_configuration(self) -> Dict[str, float]:
        """Load saved analysis parameters from configuration.
        
        Returns:
            Dictionary of analysis parameters
        """
        return self.config_manager.get_analysis_params()
    
    # ===== Directory Management =====
    
    def open_directory(self, directory_path: str, on_reload: Optional[Callable] = None) -> bool:
        """Open a new data directory and reload data.
        
        Args:
            directory_path: Path to new directory
            on_reload: Optional callback to execute after reload
            
        Returns:
            True if directory opened successfully
        """
        try:
            new_dir = Path(directory_path)
            
            if not new_dir.exists():
                print(f"Error: Directory does not exist: {directory_path}")
                return False
            
            # Update global DATA_DIR
            config.DATA_DIR = new_dir
            
            # Save as last opened directory
            self.config_manager.save_last_data_dir(str(new_dir))
            
            print(f"✓ Directorio cambiado a: {directory_path}")
            
            # Reload configuration from DATA.txt if available
            data_config = read_data_config(config.DATA_DIR)
            
            if data_config:
                # Update global config values
                if 'window_time' in data_config:
                    config.WINDOW_TIME = data_config['window_time']
                if 'trigger_voltage' in data_config:
                    config.TRIGGER_VOLTAGE = data_config['trigger_voltage']
                if 'num_points' in data_config:
                    config.NUM_POINTS = data_config['num_points']
                    config.SAMPLE_TIME = config.WINDOW_TIME / config.NUM_POINTS
            
            # Execute reload callback if provided
            if on_reload:
                on_reload()
            
            return True
            
        except Exception as e:
            print(f"Error opening directory: {e}")
            return False
    
    def get_last_directory(self) -> Optional[str]:
        """Get last opened directory from configuration.
        
        Returns:
            Last directory path or None
        """
        return self.config_manager.get_last_data_dir()
