"""
Baseline tracking utility for monitoring baseline changes over time.
"""
import json
from pathlib import Path
from typing import Dict, Optional
import numpy as np


class BaselineTracker:
    """Tracks baseline values over time and provides comparison statistics."""
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize baseline tracker.
        
        Args:
            history_file: Path to JSON file for storing history. 
                         Defaults to ~/.gemini/baseline_history.json
        """
        if history_file is None:
            gemini_dir = Path.home() / '.gemini'
            gemini_dir.mkdir(exist_ok=True)
            history_file = gemini_dir / 'baseline_history.json'
        
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """Load baseline history from file."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return data.get('baselines', [])
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self):
        """Save baseline history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({'baselines': self.history}, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save baseline history: {e}")
    
    def add_baseline(self, value_mv: float):
        """
        Add a new baseline value to history.
        
        Args:
            value_mv: Baseline value in millivolts
        """
        self.history.append(value_mv)
        
        # Keep only last 1000 values to prevent file from growing too large
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        self._save_history()
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistics about baseline history.
        
        Returns:
            Dictionary with 'mean', 'std', 'min', 'max', 'count', 'last'
        """
        if not self.history:
            return {
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0,
                'last': 0.0
            }
        
        values = np.array(self.history)
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'count': len(values),
            'last': float(values[-1])
        }
    
    def get_comparison(self) -> Optional[Dict[str, any]]:
        """
        Compare current baseline with historical average.
        
        Returns:
            Dictionary with:
                - 'improved': True if baseline decreased (improved), False if increased
                - 'percentage': Percentage change (positive = worse, negative = better)
                - 'arrow': '↑' or '↓'
                - 'color': 'red' or 'green'
            Returns None if no history available
        """
        if len(self.history) < 2:
            return None
        
        stats = self.get_statistics()
        current = stats['last']
        
        # Use mean of all previous values (excluding current)
        historical_mean = float(np.mean(self.history[:-1]))
        
        if historical_mean == 0:
            return None
        
        # Calculate percentage change
        change = current - historical_mean
        percentage = (change / historical_mean) * 100
        
        # Determine if improved (lower is better for baseline)
        improved = change < 0
        
        return {
            'improved': improved,
            'percentage': abs(percentage),
            'arrow': '↓' if improved else '↑',
            'color': 'green' if improved else 'red',
            'current': current,
            'historical_mean': historical_mean
        }
