"""
Waveform data loading and management.
"""
import numpy as np
from pathlib import Path
from typing import List, Tuple
from config import DATA_DIR, WINDOW_TIME, NUM_POINTS, SAMPLE_TIME


from utils.exceptions import WaveformError
from utils.file_io import read_waveform_file

class WaveformData:
    """Manages loading and accessing waveform data files."""
    
    def __init__(self, data_dir: Path = DATA_DIR):
        """
        Initialize waveform data manager.
        
        Args:
            data_dir: Directory containing waveform files
        """
        self.data_dir = Path(data_dir)
        self.waveform_files: List[Path] = []
        self.global_min_amp = 0.0
        self.global_max_amp = 0.01  # Default fallback
        self.all_amplitudes_flat = np.array([])
        self.all_max_times = []
        
    def load_files(self, pattern: str = "SiPMG_LAr_DCR1_*.txt") -> int:
        """
        Load waveform files from directory.
        
        Args:
            pattern: Glob pattern for file matching
            
        Returns:
            Number of files loaded
        """
        self.waveform_files = sorted(self.data_dir.glob(pattern))
        print(f"Loaded {len(self.waveform_files)} files.")
        
        if self.waveform_files:
            self._calculate_global_statistics()
        
        return len(self.waveform_files)
    
    def _calculate_global_statistics(self):
        """Calculate global amplitude ranges and statistics."""
        print("Calculating global scale, baseline and maxima...")
        
        min_vals = []
        max_vals = []
        all_data_list = []
        self.all_max_times = []
        
        for wf_file in self.waveform_files:
            try:
                t_half, amplitudes = read_waveform_file(wf_file)
                
                min_vals.append(np.min(amplitudes))
                max_vals.append(np.max(amplitudes))
                all_data_list.append(amplitudes)
                
                # Max time relative to trigger
                max_idx = np.argmax(amplitudes)
                time_rel = (max_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                self.all_max_times.append(time_rel)
            except WaveformError as e:
                print(f"Skipping {wf_file}: {e}")
            except Exception as e:
                print(f"Unexpected error reading {wf_file}: {e}")
        
        if all_data_list:
            self.all_amplitudes_flat = np.concatenate(all_data_list)
        
        if min_vals and max_vals:
            self.global_min_amp = min(min_vals)
            real_max = max(max_vals)
            
            # Add some padding
            margin = (real_max - self.global_min_amp) * 0.1
            self.global_min_amp -= margin
            self.global_max_amp = real_max + margin
            
            print(f"Global Scale: {self.global_min_amp*1000:.2f}mV to {self.global_max_amp*1000:.2f}mV")
    
    def read_waveform_file(self, file_path: Path) -> Tuple[float, np.ndarray]:
        """
        Read a single waveform file.
        Deprecated: Use utils.file_io.read_waveform_file instead.
        """
        return read_waveform_file(file_path)

    def get_file_count(self) -> int:
        """Get number of loaded files."""
        return len(self.waveform_files)
    
    def get_file_at_index(self, index: int) -> Path:
        """Get file path at specific index."""
        if 0 <= index < len(self.waveform_files):
            return self.waveform_files[index]
        raise IndexError(f"File index {index} out of range")
