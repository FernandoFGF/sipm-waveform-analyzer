"""
Favorites manager for persistent storage of favorite waveforms.
"""
import json
from pathlib import Path
from typing import Set


class FavoritesManager:
    """Manages favorite waveforms with persistent storage per dataset."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize favorites manager.
        
        Args:
            data_dir: Data directory (used to create dataset-specific favorites file)
        """
        self.data_dir = Path(data_dir)
        # Create favorites file in the same directory as the data
        self.favorites_file = self.data_dir / ".favorites.json"
        self.favorites: Set[str] = set()
        self.load_favorites()
    
    def load_favorites(self) -> Set[str]:
        """
        Load favorites from file.
        
        Returns:
            Set of favorite filenames
        """
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r') as f:
                    data = json.load(f)
                    self.favorites = set(data.get('favorites', []))
                    print(f"Loaded {len(self.favorites)} favorites from {self.favorites_file.name}")
            except Exception as e:
                print(f"Error loading favorites: {e}")
                self.favorites = set()
        else:
            self.favorites = set()
        
        return self.favorites
    
    def save_favorites(self):
        """Save favorites to file."""
        try:
            data = {
                'favorites': list(self.favorites),
                'dataset': self.data_dir.name
            }
            with open(self.favorites_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[OK] Saved {len(self.favorites)} favorites")
        except Exception as e:
            print(f"Error saving favorites: {e}")
    
    def add_favorite(self, filename: str):
        """
        Add a waveform to favorites.
        
        Args:
            filename: Waveform filename to add
        """
        self.favorites.add(filename)
        self.save_favorites()
    
    def remove_favorite(self, filename: str):
        """
        Remove a waveform from favorites.
        
        Args:
            filename: Waveform filename to remove
        """
        if filename in self.favorites:
            self.favorites.discard(filename)
            self.save_favorites()
    
    def is_favorite(self, filename: str) -> bool:
        """
        Check if a waveform is in favorites.
        
        Args:
            filename: Waveform filename to check
            
        Returns:
            True if in favorites, False otherwise
        """
        return filename in self.favorites
    
    def get_favorites(self) -> Set[str]:
        """
        Get all favorite filenames.
        
        Returns:
            Set of favorite filenames
        """
        return self.favorites.copy()
    
    def clear_favorites(self):
        """Clear all favorites."""
        self.favorites.clear()
        self.save_favorites()
