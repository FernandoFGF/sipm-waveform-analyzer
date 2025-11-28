"""
Results caching system for analysis optimization.
"""
import hashlib
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class ResultsCache:
    """Cache for storing and retrieving analysis results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize results cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_cache_key(self, files: list, params: Dict[str, Any]) -> str:
        """
        Generate unique cache key from files and parameters.
        
        Args:
            files: List of file paths
            params: Dictionary of analysis parameters
            
        Returns:
            MD5 hash string as cache key
        """
        # Sort files for consistent hashing
        sorted_files = sorted([str(f) for f in files])
        
        # Sort params for consistent hashing
        sorted_params = dict(sorted(params.items()))
        
        # Create combined string
        combined = str(sorted_files) + str(sorted_params)
        
        # Generate MD5 hash
        key = hashlib.md5(combined.encode()).hexdigest()
        
        return key
    
    def has(self, key: str) -> bool:
        """
        Check if cache entry exists.
        
        Args:
            key: Cache key
            
        Returns:
            True if cache exists, False otherwise
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        return cache_file.exists()
    
    def save(self, key: str, results: Any, params: Dict[str, Any]):
        """
        Save results to cache.
        
        Args:
            key: Cache key
            results: Analysis results object
            params: Parameters used for analysis
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        
        # Save results
        with open(cache_file, 'wb') as f:
            pickle.dump(results, f)
        
        # Update metadata
        self.metadata[key] = {
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'file_count': getattr(results, 'total_events', 0) if hasattr(results, 'total_events') else 0
        }
        self._save_metadata()
        
        print(f"✓ Results cached (key: {key[:8]}...)")
    
    def load(self, key: str) -> Optional[Any]:
        """
        Load results from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached results or None if not found
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                results = pickle.load(f)
            
            print(f"✓ Results loaded from cache (key: {key[:8]}...)")
            return results
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None
    
    def clear(self):
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        
        self.metadata = {}
        self._save_metadata()
        
        print("✓ Cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached results.
        
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'num_entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'entries': self.metadata
        }
    
    def list_cached_analyses(self) -> list:
        """
        List all cached analyses with their parameters.
        
        Returns:
            List of dictionaries with cache information
        """
        analyses = []
        
        for key, meta in self.metadata.items():
            analyses.append({
                'key': key,
                'timestamp': meta['timestamp'],
                'params': meta['params'],
                'file_count': meta.get('file_count', 0)
            })
        
        # Sort by timestamp (newest first)
        analyses.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return analyses
