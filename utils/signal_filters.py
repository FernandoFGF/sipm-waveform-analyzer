"""
Signal filtering utilities for waveform processing.
"""
import numpy as np
from scipy.signal import savgol_filter, wiener, correlate


def apply_savitzky_golay(amplitudes, window_length=11, polyorder=3):
    """
    Apply Savitzky-Golay filter for smoothing while preserving peaks.
    
    Args:
        amplitudes: Array of amplitude values
        window_length: Length of filter window (must be odd)
        polyorder: Order of polynomial fit
        
    Returns:
        Filtered amplitudes
    """
    # Ensure window_length is odd
    if window_length % 2 == 0:
        window_length += 1
    
    # Ensure window_length > polyorder
    if window_length <= polyorder:
        window_length = polyorder + 2
        if window_length % 2 == 0:
            window_length += 1
    
    return savgol_filter(amplitudes, window_length, polyorder)


def apply_matched_filter(amplitudes, template=None):
    """
    Apply matched filter using pulse template.
    
    Args:
        amplitudes: Array of amplitude values
        template: Template pulse (if None, auto-generated)
        
    Returns:
        Filtered amplitudes
    """
    if template is None:
        # Auto-generate simple pulse template
        template = generate_pulse_template(amplitudes)
    
    # Normalize template
    template = template / np.sum(template**2)
    
    # Apply matched filter
    filtered = correlate(amplitudes, template, mode='same')
    
    return filtered


def apply_wiener_filter(amplitudes, mysize=5):
    """
    Apply Wiener filter for noise reduction.
    
    Args:
        amplitudes: Array of amplitude values
        mysize: Size of local window for noise estimation
        
    Returns:
        Filtered amplitudes
    """
    return wiener(amplitudes, mysize=mysize)


def apply_wavelet_denoise(amplitudes, wavelet='db4', level=4, mode='soft'):
    """
    Apply wavelet denoising.
    
    Args:
        amplitudes: Array of amplitude values
        wavelet: Wavelet type ('db4', 'sym4', 'coif3', etc.)
        level: Decomposition level
        mode: Thresholding mode ('soft' or 'hard')
        
    Returns:
        Denoised amplitudes
    """
    try:
        import pywt
    except ImportError:
        print("Warning: pywt not installed. Wavelet denoising not available.")
        return amplitudes
    
    # Decompose signal
    coeffs = pywt.wavedec(amplitudes, wavelet, level=level)
    
    # Calculate threshold using MAD (Median Absolute Deviation)
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(amplitudes)))
    
    # Apply threshold to detail coefficients
    coeffs_thresh = [coeffs[0]]  # Keep approximation coefficients
    for c in coeffs[1:]:
        coeffs_thresh.append(pywt.threshold(c, threshold, mode=mode))
    
    # Reconstruct signal
    return pywt.waverec(coeffs_thresh, wavelet)


def generate_pulse_template(amplitudes, window_size=50):
    """
    Generate a simple pulse template from the signal.
    
    Args:
        amplitudes: Array of amplitude values
        window_size: Size of template window
        
    Returns:
        Pulse template
    """
    # Find the peak
    peak_idx = np.argmax(np.abs(amplitudes))
    
    # Extract window around peak
    start = max(0, peak_idx - window_size // 2)
    end = min(len(amplitudes), peak_idx + window_size // 2)
    
    template = amplitudes[start:end].copy()
    
    # Normalize
    if len(template) > 0:
        template = template - np.mean(template)
        if np.max(np.abs(template)) > 0:
            template = template / np.max(np.abs(template))
    
    return template


def calculate_snr_improvement(original, filtered):
    """
    Calculate SNR improvement in dB.
    
    Args:
        original: Original signal
        filtered: Filtered signal
        
    Returns:
        SNR improvement in dB
    """
    # Estimate signal as the peak region
    peak_idx = np.argmax(np.abs(original))
    signal_window = slice(max(0, peak_idx - 20), min(len(original), peak_idx + 20))
    
    # Estimate noise from baseline region (first 100 samples)
    noise_window = slice(0, min(100, len(original) // 4))
    
    # Calculate SNR for original
    signal_power_orig = np.var(original[signal_window])
    noise_power_orig = np.var(original[noise_window])
    snr_orig = signal_power_orig / noise_power_orig if noise_power_orig > 0 else 1
    
    # Calculate SNR for filtered
    signal_power_filt = np.var(filtered[signal_window])
    noise_power_filt = np.var(filtered[noise_window])
    snr_filt = signal_power_filt / noise_power_filt if noise_power_filt > 0 else 1
    
    # SNR improvement in dB
    if snr_orig > 0:
        improvement_db = 10 * np.log10(snr_filt / snr_orig)
    else:
        improvement_db = 0
    
    return improvement_db


def calculate_rms_noise(amplitudes, noise_window_size=100):
    """
    Calculate RMS noise from baseline region.
    
    Args:
        amplitudes: Array of amplitude values
        noise_window_size: Size of baseline window
        
    Returns:
        RMS noise value
    """
    baseline = amplitudes[:min(noise_window_size, len(amplitudes) // 4)]
    return np.sqrt(np.mean(baseline**2))
