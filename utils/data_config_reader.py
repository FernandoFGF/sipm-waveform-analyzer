"""
Utility to read configuration from DATA.txt file.
"""
from pathlib import Path
from typing import Dict, Optional


def read_data_config(data_dir: Path) -> Optional[Dict]:
    """
    Read configuration from DATA.txt file in the data directory.
    
    Args:
        data_dir: Path to the data directory
        
    Returns:
        Dictionary with configuration values or None if file not found
    """
    data_file = data_dir / "DATA.txt"
    
    if not data_file.exists():
        print(f"Warning: DATA.txt not found in {data_dir}")
        return None
    
    config = {}
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse different configuration lines
                if "Time base scale:" in line:
                    # Extract: "Time base scale: 5e-07 s" -> 5e-07
                    parts = line.split(":")
                    if len(parts) >= 2:
                        value_str = parts[1].strip().split()[0]  # Get first part before 's'
                        config['time_base_scale'] = float(value_str)
                
                elif "Trigger (0.5PE):" in line:
                    # Extract: "Trigger (0.5PE): 0.0 v" -> 0.0
                    parts = line.split(":")
                    if len(parts) >= 2:
                        value_str = parts[1].strip().split()[0]  # Get first part before 'v'
                        config['trigger_voltage'] = float(value_str)
                
                elif "Resolucion(SRATE):" in line:
                    # Extract: "Resolucion(SRATE): 50000000.0 Sa/s" -> 50000000.0
                    parts = line.split(":")
                    if len(parts) >= 2:
                        value_str = parts[1].strip().split()[0]
                        config['sample_rate'] = float(value_str)
                
                elif "Num de puntos(real):" in line:
                    # Extract: "Num de puntos(real): 4081" -> 4081
                    parts = line.split(":")
                    if len(parts) >= 2:
                        value_str = parts[1].strip()
                        config['num_points'] = int(float(value_str))
        
        # Calculate WINDOW_TIME as time_base_scale * 10
        if 'time_base_scale' in config:
            config['window_time'] = config['time_base_scale'] * 10
        
        print(f"✓ Loaded configuration from DATA.txt:")
        print(f"  Time base scale: {config.get('time_base_scale', 'N/A')} s")
        print(f"  Window time: {config.get('window_time', 'N/A')} s")
        print(f"  Trigger voltage: {config.get('trigger_voltage', 'N/A')} V")
        print(f"  Num points: {config.get('num_points', 'N/A')}")
        
        return config
        
    except Exception as e:
        print(f"Error reading DATA.txt: {e}")
        return None
