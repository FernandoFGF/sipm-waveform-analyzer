"""
Pulse analysis utilities for advanced SiPM characterization.
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm
from typing import Tuple, List, Dict
from sklearn.decomposition import PCA


def calculate_rise_time(amplitudes: np.ndarray, time_array: np.ndarray, 
                       peak_idx: int, baseline: float) -> float:
    """
    Calculate 10%-90% rise time of a pulse.
    
    Args:
        amplitudes: Waveform amplitudes
        time_array: Time values
        peak_idx: Index of peak maximum
        baseline: Baseline value
        
    Returns:
        Rise time in seconds
    """
    peak_amp = amplitudes[peak_idx]
    amp_range = peak_amp - baseline
    
    # 10% and 90% levels
    level_10 = baseline + 0.1 * amp_range
    level_90 = baseline + 0.9 * amp_range
    
    # Find indices before peak
    before_peak = amplitudes[:peak_idx]
    
    # Find crossing points
    idx_10 = np.where(before_peak >= level_10)[0]
    idx_90 = np.where(before_peak >= level_90)[0]
    
    if len(idx_10) == 0 or len(idx_90) == 0:
        return np.nan
    
    t_10 = time_array[idx_10[0]]
    t_90 = time_array[idx_90[0]]
    
    return t_90 - t_10


def calculate_fall_time(amplitudes: np.ndarray, time_array: np.ndarray, 
                       peak_idx: int, baseline: float) -> float:
    """
    Calculate 90%-10% fall time of a pulse.
    
    Args:
        amplitudes: Waveform amplitudes
        time_array: Time values
        peak_idx: Index of peak maximum
        baseline: Baseline value
        
    Returns:
        Fall time in seconds
    """
    peak_amp = amplitudes[peak_idx]
    amp_range = peak_amp - baseline
    
    # 90% and 10% levels
    level_90 = baseline + 0.9 * amp_range
    level_10 = baseline + 0.1 * amp_range
    
    # Find indices after peak
    after_peak = amplitudes[peak_idx:]
    
    # Find crossing points (going down)
    idx_90 = np.where(after_peak <= level_90)[0]
    idx_10 = np.where(after_peak <= level_10)[0]
    
    if len(idx_90) == 0 or len(idx_10) == 0:
        return np.nan
    
    t_90 = time_array[peak_idx + idx_90[0]]
    t_10 = time_array[peak_idx + idx_10[0]]
    
    return t_10 - t_90


def calculate_fwhm(amplitudes: np.ndarray, time_array: np.ndarray, 
                   peak_idx: int, baseline: float) -> float:
    """
    Calculate Full Width at Half Maximum.
    
    Args:
        amplitudes: Waveform amplitudes
        time_array: Time values
        peak_idx: Index of peak maximum
        baseline: Baseline value
        
    Returns:
        FWHM in seconds
    """
    peak_amp = amplitudes[peak_idx]
    half_max = baseline + (peak_amp - baseline) / 2
    
    # Find left crossing
    left_side = amplitudes[:peak_idx]
    left_cross = np.where(left_side >= half_max)[0]
    
    # Find right crossing
    right_side = amplitudes[peak_idx:]
    right_cross = np.where(right_side <= half_max)[0]
    
    if len(left_cross) == 0 or len(right_cross) == 0:
        return np.nan
    
    t_left = time_array[left_cross[0]]
    t_right = time_array[peak_idx + right_cross[0]]
    
    return t_right - t_left


def fit_exponential_recovery(delta_t: np.ndarray, amplitudes: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """
    Fit exponential decay to recovery time data.
    
    Args:
        delta_t: Time differences (seconds)
        amplitudes: Afterpulse amplitudes
        
    Returns:
        Tuple of (tau, A0, fitted_curve)
    """
    def exponential(t, A0, tau):
        return A0 * np.exp(-t / tau)
    
    # Initial guess
    A0_init = np.max(amplitudes)
    tau_init = np.median(delta_t)
    
    try:
        popt, _ = curve_fit(
            exponential,
            delta_t,
            amplitudes,
            p0=[A0_init, tau_init],
            maxfev=10000,
            bounds=([0, 0], [np.inf, np.inf])
        )
        
        A0, tau = popt
        
        # Generate fitted curve
        t_fit = np.linspace(np.min(delta_t), np.max(delta_t), 200)
        fitted_curve = exponential(t_fit, A0, tau)
        
        return tau, A0, fitted_curve
    except:
        return np.nan, np.nan, np.array([])


def extract_pulse_template(waveforms: List[np.ndarray], peak_indices: List[int],
                          window_size: int = 100) -> np.ndarray:
    """
    Average pulses to create a template.
    
    Args:
        waveforms: List of waveform arrays
        peak_indices: List of peak indices for each waveform
        window_size: Number of samples around peak to extract
        
    Returns:
        Averaged pulse template
    """
    aligned_pulses = []
    
    for wf, peak_idx in zip(waveforms, peak_indices):
        # Extract window around peak
        start = max(0, peak_idx - window_size // 2)
        end = min(len(wf), peak_idx + window_size // 2)
        
        pulse = wf[start:end]
        
        # Pad if necessary
        if len(pulse) < window_size:
            pulse = np.pad(pulse, (0, window_size - len(pulse)), mode='edge')
        
        aligned_pulses.append(pulse[:window_size])
    
    # Average
    template = np.mean(aligned_pulses, axis=0)
    return template


def perform_pulse_pca(pulse_features: np.ndarray) -> Tuple[np.ndarray, PCA]:
    """
    Perform PCA on pulse shape features.
    
    Args:
        pulse_features: Array of shape (n_pulses, n_features)
        
    Returns:
        Tuple of (transformed_data, pca_model)
    """
    pca = PCA(n_components=2)
    transformed = pca.fit_transform(pulse_features)
    
    return transformed, pca


def calculate_pulse_area(amplitudes: np.ndarray, time_array: np.ndarray,
                        peak_idx: int, baseline: float, 
                        window_samples: int = 50) -> float:
    """
    Calculate integrated area of pulse above baseline.
    
    Args:
        amplitudes: Waveform amplitudes
        time_array: Time values
        peak_idx: Index of peak maximum
        baseline: Baseline value
        window_samples: Number of samples to integrate around peak
        
    Returns:
        Integrated area (V*s)
    """
    start = max(0, peak_idx - window_samples // 2)
    end = min(len(amplitudes), peak_idx + window_samples // 2)
    
    pulse_region = amplitudes[start:end]
    time_region = time_array[start:end]
    
    # Subtract baseline
    signal_above_baseline = pulse_region - baseline
    signal_above_baseline[signal_above_baseline < 0] = 0
    
    # Integrate using trapezoidal rule
    area = np.trapz(signal_above_baseline, time_region)
    
    return area


def fit_gaussian_jitter(peak_times: np.ndarray) -> Tuple[float, float, float]:
    """
    Fit Gaussian to peak time distribution for jitter analysis.
    
    Args:
        peak_times: Array of peak times
        
    Returns:
        Tuple of (mu, sigma, fwhm)
    """
    mu, sigma = norm.fit(peak_times)
    
    # FWHM = 2.355 * sigma for Gaussian
    fwhm = 2.355 * sigma
    
    return mu, sigma, fwhm
