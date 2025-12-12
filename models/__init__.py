"""Package initialization for models."""
from .waveform_data import WaveformData
from .analysis_results import AnalysisResults, WaveformResult
from .peak_analyzer import PeakAnalyzer
from .baseline_tracker import BaselineTracker
from .results_cache import ResultsCache
from .favorites_manager import FavoritesManager

# Optional: do not export large modules with many functions if only specific classes are desired, 
# or just leave them importable as submodules.
