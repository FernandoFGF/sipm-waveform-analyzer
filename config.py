"""
Global configuration for the Peak Finder application.
"""
from pathlib import Path

# ============================================================================
# DATA CONFIGURATION
# ============================================================================
DATA_DIR = Path(r"c:\Users\Ferna\Desktop\Laboratorio\analisis\SiPMG_LAr_DCR1_AMP")

# ============================================================================
# WAVEFORM PARAMETERS
# ============================================================================
WINDOW_TIME = 5e-6  # 5 microseconds
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
