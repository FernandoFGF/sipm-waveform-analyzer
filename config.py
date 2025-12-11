"""
Global configuration for the Peak Finder application.
"""
from pathlib import Path

# ============================================================================
# DATA CONFIGURATION
# ============================================================================
# Default data directory (can be changed at runtime)
_DEFAULT_DATA_DIR = Path(r"c:\Users\Ferna\Desktop\Laboratorio\analisis\SiPM4_LN2_DCR1")

# Try to load last opened directory from user config
try:
    import json
    _config_file = Path("user_config.json")
    if _config_file.exists():
        with open(_config_file, 'r') as _f:
            _user_config = json.load(_f)
            _last_dir = _user_config.get('last_data_dir')
            if _last_dir and Path(_last_dir).exists():
                DATA_DIR = Path(_last_dir)
            else:
                DATA_DIR = _DEFAULT_DATA_DIR
    else:
        DATA_DIR = _DEFAULT_DATA_DIR
except Exception:
    DATA_DIR = _DEFAULT_DATA_DIR

# ============================================================================
# WAVEFORM PARAMETERS
# ============================================================================
# These will be loaded from DATA.txt if available, otherwise use defaults
WINDOW_TIME = 5e-6  # 5 microseconds (default)
TRIGGER_VOLTAGE = 0.0  # Trigger voltage in V (default)

# Auto-detect NUM_POINTS from the first data file in the directory
# File format: line 1 (metadata/time), line 2 (blank), lines 3 to N-1 (data), line N (blank)
# So NUM_POINTS = total_lines - 3
try:
    # Try to load from DATA.txt first
    from pathlib import Path as _Path
    _data_txt = DATA_DIR / "DATA.txt"
    if _data_txt.exists():
        with open(_data_txt, 'r', encoding='utf-8') as _f:
            for _line in _f:
                if "Time base scale:" in _line:
                    _time_base = float(_line.split(":")[1].strip().split()[0])
                    WINDOW_TIME = _time_base * 10
                elif "Trigger (0.5PE):" in _line:
                    TRIGGER_VOLTAGE = float(_line.split(":")[1].strip().split()[0])
                elif "Num de puntos(real):" in _line:
                    NUM_POINTS = int(float(_line.split(":")[1].strip()))
    
    # If NUM_POINTS not set from DATA.txt, try from waveform files
    if 'NUM_POINTS' not in locals():
        # Use directory name to find the correct waveform files
        dir_name = DATA_DIR.name
        pattern = f"{dir_name}_*.txt"
        first_file = next(DATA_DIR.glob(pattern))
        
        with open(first_file, 'r') as f:
            total_lines = sum(1 for _ in f)
        NUM_POINTS = total_lines - 2
except (StopIteration, Exception):
    # No files found or error reading - use a reasonable default
    NUM_POINTS = 4081

SAMPLE_TIME = WINDOW_TIME / NUM_POINTS



# ============================================================================
# DEFAULT ANALYSIS PARAMETERS
# ============================================================================
DEFAULT_PROMINENCE_PCT = 2.0  # Prominence in range 0.1-5%
DEFAULT_WIDTH_TIME = 0.2e-6  # Minimum peak width in seconds
DEFAULT_MIN_DIST_TIME = 0.05e-6  # Minimum distance between peaks in seconds
DEFAULT_BASELINE_PCT = 85.0  # Baseline percentile range
DEFAULT_MAX_DIST_PCT = 99.0  # Max distance zone percentile
DEFAULT_AFTERPULSE_PCT = 80.0  # Afterpulse zone percentile

# ============================================================================
# UI CONFIGURATION
# ============================================================================
UI_THEME = "Dark"
UI_COLOR_THEME = "blue"
MAIN_WINDOW_SIZE = "1600x900"
POPUP_WINDOW_SIZE_TEMPORAL = "800x600"
POPUP_WINDOW_SIZE_WAVEFORMS = "1200x800"

# ============================================================================
# PLOT COLORS
# ============================================================================
COLOR_ACCEPTED = '#2ecc71'  # Greenish
COLOR_REJECTED = '#e74c3c'  # Reddish
COLOR_AFTERPULSE = '#f1c40f'  # Yellowish
COLOR_REJECTED_AFTERPULSE = '#9b59b6'  # Purple
COLOR_WAVEFORM_OVERLAY = '#1E90FF'  # DodgerBlue
