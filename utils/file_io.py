"""
File I/O utilities for reading waveforms and exporting results.
"""
import csv
import json
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime

from utils.exceptions import WaveformError
from config import SAMPLE_TIME, WINDOW_TIME

def read_waveform_file(file_path: Path) -> Tuple[float, np.ndarray]:
    """
    Read a single waveform file.
    
    Args:
        file_path: Path to waveform file
        
    Returns:
        Tuple of (t_half, amplitudes)
        
    Raises:
        WaveformError: If file cannot be read or parsed
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 3:
            raise WaveformError("File too short")
            
        t_half = float(lines[0].strip())
        amplitudes = np.array([float(line.strip()) for line in lines[2:] if line.strip()])
        
        return t_half, amplitudes
    except (IOError, ValueError) as e:
        raise WaveformError(f"Failed to read waveform file: {e}")

def export_to_csv(data: list, headers: list, filepath: str):
    """
    Generic CSV export.
    
    Args:
        data: List of rows (lists)
        headers: List of column headers
        filepath: Output file path
    """
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)
    print(f"✓ Exported to {filepath}")

def export_to_json(data: Dict[str, Any], filepath: str):
    """
    Generic JSON export.
    
    Args:
        data: Dictionary to export
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Exported to {filepath}")
