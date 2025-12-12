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
def recalculate_config(data_dir_path=None):
    """
    Recalculate global configuration parameters based on the data directory.
    This should be called whenever the data directory changes.
    """
    global DATA_DIR, WINDOW_TIME, TRIGGER_VOLTAGE, NUM_POINTS, SAMPLE_TIME
    
    if data_dir_path:
        DATA_DIR = Path(data_dir_path)
        
    # Default values
    WINDOW_TIME = 5e-6
    TRIGGER_VOLTAGE = 0.0
    
    # Reset NUM_POINTS to ensure it's recalculated
    # We use a local variable first to avoid issues if we can't find files
    calculated_num_points = 4081 

    try:
        # Try to load from DATA.txt first
        data_txt = DATA_DIR / "DATA.txt"
        if data_txt.exists():
            with open(data_txt, 'r', encoding='utf-8') as f:
                for line in f:
                    if "Time base scale:" in line:
                        time_base = float(line.split(":")[1].strip().split()[0])
                        WINDOW_TIME = time_base * 10
                    elif "Trigger (0.5PE):" in line:
                        TRIGGER_VOLTAGE = float(line.split(":")[1].strip().split()[0])
                    # Note: We explicitly IGNORE "Num de puntos" from DATA.txt to ensure
                    # Decimation filters (which reduce points) work correctly by counting lines below.
        
        # Always calculate NUM_POINTS from actual file lines
        # This handles both normal and decimated files correctly
        dir_name = DATA_DIR.name
        pattern = f"{dir_name}_*.txt"
        found_file = False
        
        try:
            first_file = next(DATA_DIR.glob(pattern))
            with open(first_file, 'r') as f:
                total_lines = sum(1 for _ in f)
            calculated_num_points = total_lines - 2
            found_file = True
        except (StopIteration, Exception):
            pass
            
        if not found_file:
            # Fallback: try any .txt file that isn't DATA.txt
            try:
                first_file = next(f for f in DATA_DIR.glob("*.txt") if f.name != "DATA.txt")
                with open(first_file, 'r') as f:
                    total_lines = sum(1 for _ in f)
                calculated_num_points = total_lines - 2
            except:
                pass

    except Exception as e:
        print(f"Error recalculating config: {e}")
        
    NUM_POINTS = calculated_num_points
    # Avoid division by zero
    if NUM_POINTS <= 0:
        NUM_POINTS = 4081
        
    SAMPLE_TIME = WINDOW_TIME / NUM_POINTS
    # print(f"Config updated: Window={WINDOW_TIME*1e6:.1f}us, Points={NUM_POINTS}, SampleT={SAMPLE_TIME*1e9:.2f}ns")


# Initial calculation on import
recalculate_config()



# ============================================================================
# DEFAULT ANALYSIS PARAMETERS
# ============================================================================
DEFAULT_PROMINENCE_PCT = 2.0  # Prominence in range 0.1-5%
DEFAULT_WIDTH_TIME = 0.2e-6  # Minimum peak width in seconds
DEFAULT_MIN_DIST_TIME = 0.05e-6  # Minimum distance between peaks in seconds
DEFAULT_BASELINE_PCT = 85.0  # Baseline percentile range
DEFAULT_MAX_DIST_PCT = 99.0  # Max distance zone percentile
DEFAULT_NEGATIVE_TRIGGER_MV = -10.0  # Negative trigger threshold in mV (reject if any peak below this)

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
