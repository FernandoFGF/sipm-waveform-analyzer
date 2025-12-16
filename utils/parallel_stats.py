"""
Helper functions for parallel waveform statistics calculation.
"""
import numpy as np
from pathlib import Path


def process_file_for_stats(wf_file):
    """
    Process single file for statistics (standalone function for multiprocessing).
    
    Args:
        wf_file: Path to waveform file
        
    Returns:
        Dictionary with min, max, and max_time, or None if error
    """
    try:
        from utils.file_io import read_waveform_file
        from config import WINDOW_TIME, NUM_POINTS
        
        t_half, amplitudes = read_waveform_file(wf_file)
        
        min_val = np.min(amplitudes)
        max_val = np.max(amplitudes)
        
        # Max time relative to trigger
        original_sample_time = WINDOW_TIME / NUM_POINTS
        max_idx = np.argmax(amplitudes)
        time_rel = (max_idx * original_sample_time) - (WINDOW_TIME / 2)
        
        return {
            'min': min_val,
            'max': max_val,
            'max_time': time_rel
        }
    except Exception:
        return None
