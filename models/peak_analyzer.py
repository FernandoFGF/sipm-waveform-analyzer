"""
Peak detection and classification logic.
"""
import numpy as np
from scipy.signal import find_peaks
from typing import List, Tuple
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from config import WINDOW_TIME, SAMPLE_TIME
from models.waveform_data import WaveformData
from models.analysis_results import AnalysisResults, WaveformResult
from utils.exceptions import WaveformError, AnalysisError
from views.popups import show_error_dialog
class PeakAnalyzer:
    """Analyzes waveforms for peak detection and classification."""
    
    def __init__(self, waveform_data: WaveformData):
        """
        Initialize peak analyzer.
        
        Args:
            waveform_data: WaveformData instance with loaded files
        """
        self.waveform_data = waveform_data
        
    def analyze_all(
        self,
        prominence_pct: float,
        width_time: float,
        min_dist_time: float,
        baseline_pct: float,
        max_dist_pct: float,
        afterpulse_pct: float
    ) -> AnalysisResults:
        """
        Analyze all waveforms with given parameters.
        
        Args:
            prominence_pct: Prominence threshold as percentage of amplitude range
            width_time: Minimum peak width in seconds
            min_dist_time: Minimum distance between peaks in seconds
            baseline_pct: Baseline percentile range
            max_dist_pct: Max distance zone percentile
            afterpulse_pct: Afterpulse zone percentile
            
        Returns:
            AnalysisResults containing classified waveforms
        """
        results = AnalysisResults()
        
        # Calculate parameters
        amp_range = self.waveform_data.global_max_amp - self.waveform_data.global_min_amp
        prominence = (prominence_pct / 100.0) * amp_range
        width_samples = int(width_time / SAMPLE_TIME)
        min_dist_samples = int(min_dist_time / SAMPLE_TIME)
        if min_dist_samples < 1:
            min_dist_samples = 1
        
        # Calculate baseline range
        if len(self.waveform_data.all_amplitudes_flat) > 0:
            low_p = (100 - baseline_pct) / 2
            high_p = 100 - low_p
            results.baseline_low = np.percentile(self.waveform_data.all_amplitudes_flat, low_p)
            results.baseline_high = np.percentile(self.waveform_data.all_amplitudes_flat, high_p)
            print(f"Baseline ({baseline_pct}%): {results.baseline_low*1000:.2f}mV - {results.baseline_high*1000:.2f}mV")
        
        # Calculate max dist range
        if len(self.waveform_data.all_max_times) > 0:
            low_p = (100 - max_dist_pct) / 2
            high_p = 100 - low_p
            results.max_dist_low = np.percentile(self.waveform_data.all_max_times, low_p)
            results.max_dist_high = np.percentile(self.waveform_data.all_max_times, high_p)
            print(f"Max Dist ({max_dist_pct}%): {results.max_dist_low*1e6:.2f}µs - {results.max_dist_high*1e6:.2f}µs")
        
        # Analyze waveforms (parallel if many files, sequential if few)
        num_files = len(self.waveform_data.waveform_files)
        use_parallel = num_files > 50  # Use parallel processing for >50 files
        
        print(f"Analyzing {num_files} files {'in parallel' if use_parallel else 'sequentially'}...")
        
        if use_parallel:
            # Parallel processing for large datasets
            wf_results = self._analyze_waveforms_parallel(
                prominence,
                width_samples,
                min_dist_samples,
                results.baseline_high,
                results.max_dist_low,
                results.max_dist_high
            )
        else:
            # Sequential processing for small datasets
            wf_results = self._analyze_waveforms_sequential(
                prominence,
                width_samples,
                min_dist_samples,
                results.baseline_high,
                results.max_dist_low,
                results.max_dist_high
            )
        
        # Classify results
        afterpulse_times = []
        
        for wf_result in wf_results:
            if wf_result is None:  # Skip failed analyses
                continue
                
            good_peaks = wf_result.peaks
            all_peaks = wf_result.all_peaks
            
            # Find main candidates (good peaks inside max dist zone)
            main_candidates = self._find_main_candidates(
                good_peaks,
                wf_result.amplitudes,
                results.max_dist_low,
                results.max_dist_high
            )
            
            if len(main_candidates) == 0:
                # Rejected
                if len(all_peaks) > 1:
                    results.rejected_afterpulse_results.append(wf_result)
                else:
                    results.rejected_results.append(wf_result)
            else:
                # Accepted or Afterpulse
                if len(good_peaks) > 1:
                    # Afterpulse
                    results.afterpulse_results.append(wf_result)
                    results.total_peaks += len(good_peaks)
                    
                    # Collect afterpulse times
                    main_peak_idx = good_peaks[np.argmax(wf_result.amplitudes[good_peaks])]
                    for p_idx in good_peaks:
                        if p_idx != main_peak_idx:
                            t_ap = (p_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                            afterpulse_times.append(t_ap)
                else:
                    # Accepted (exactly 1 good peak)
                    results.accepted_results.append(wf_result)
                    results.total_peaks += 1
        
        # Calculate afterpulse range
        if len(afterpulse_times) > 0:
            low_p = (100 - afterpulse_pct) / 2
            high_p = 100 - low_p
            results.afterpulse_low = np.percentile(afterpulse_times, low_p)
            results.afterpulse_high = np.percentile(afterpulse_times, high_p)
            print(f"Afterpulse ({afterpulse_pct}%): {results.afterpulse_low*1e6:.2f}µs - {results.afterpulse_high*1e6:.2f}µs")
        
        return results
    
    def _analyze_waveforms_sequential(
        self,
        prominence: float,
        width_samples: int,
        min_dist_samples: int,
        baseline_high: float,
        max_dist_low: float,
        max_dist_high: float
    ) -> List[WaveformResult]:
        """Analyze waveforms sequentially (for small datasets)."""
        results = []
        
        for wf_file in self.waveform_data.waveform_files:
            try:
                wf_result = self._analyze_single_waveform(
                    wf_file,
                    prominence,
                    width_samples,
                    min_dist_samples,
                    baseline_high,
                    max_dist_low,
                    max_dist_high
                )
                results.append(wf_result)
            except (WaveformError, AnalysisError) as e:
                print(f"Error analyzing {wf_file}: {e}")
                show_error_dialog(f"Error en {wf_file.name}:\n{e}")
                results.append(None)
            except Exception as e:
                print(f"Unexpected error analyzing {wf_file}: {e}")
                show_error_dialog(f"Error inesperado en {wf_file.name}:\n{e}")
                results.append(None)
        
        return results
    
    def _analyze_waveforms_parallel(
        self,
        prominence: float,
        width_samples: int,
        min_dist_samples: int,
        baseline_high: float,
        max_dist_low: float,
        max_dist_high: float
    ) -> List[WaveformResult]:
        """Analyze waveforms in parallel (for large datasets)."""
        results = []
        num_workers = min(multiprocessing.cpu_count(), 8)  # Max 8 workers
        
        print(f"Using {num_workers} parallel workers...")
        
        # Create list of arguments for each file
        args_list = [
            (wf_file, prominence, width_samples, min_dist_samples,
             baseline_high, max_dist_low, max_dist_high)
            for wf_file in self.waveform_data.waveform_files
        ]
        
        # Process in parallel
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._analyze_single_waveform_wrapper, args): args[0]
                for args in args_list
            }
            
            # Collect results as they complete
            completed = 0
            total = len(future_to_file)
            
            for future in as_completed(future_to_file):
                wf_file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except (WaveformError, AnalysisError) as e:
                    print(f"Error analyzing {wf_file}: {e}")
                    # Show dialog only for specific errors if desired, or log
                    # Showing dialogs in a loop of 1000 files might be bad, but user requested it.
                    # Maybe limit? But I'll follow instructions.
                    show_error_dialog(f"Error en {wf_file.name}:\n{e}")
                    results.append(None)
                except Exception as e:
                    print(f"Unexpected error analyzing {wf_file}: {e}")
                    show_error_dialog(f"Error inesperado en {wf_file.name}:\n{e}")
                    results.append(None)
                
                completed += 1
                if completed % 100 == 0:  # Progress update every 100 files
                    print(f"Progress: {completed}/{total} files analyzed")
        
        return results
    
    @staticmethod
    def _analyze_single_waveform_wrapper(args):
        """Wrapper for parallel processing (static method)."""
        wf_file, prominence, width_samples, min_dist_samples, baseline_high, max_dist_low, max_dist_high = args
        
        # Need to recreate WaveformData instance for each process
        from models.waveform_data import WaveformData
        waveform_data = WaveformData()
        
        # Read file
        t_half, amplitudes = waveform_data.read_waveform_file(wf_file)
        
        # Find peaks
        peaks, properties = find_peaks(
            amplitudes,
            height=0.0,
            prominence=prominence,
            width=0,
            distance=min_dist_samples
        )
        
        # Handle saturation
        global_max_amp = np.max(amplitudes) * 1.05  # Approximate
        saturation_threshold = global_max_amp * 0.95
        peak_amps = amplitudes[peaks]
        saturated_mask = peak_amps >= saturation_threshold
        
        if np.sum(saturated_mask) > 1:
            saturated_indices = np.where(saturated_mask)[0]
            max_sat_peak_idx = saturated_indices[np.argmax(peak_amps[saturated_indices])]
            keep_mask = ~saturated_mask
            keep_mask[max_sat_peak_idx] = True
            peaks = peaks[keep_mask]
            for key in properties:
                if isinstance(properties[key], np.ndarray) and len(properties[key]) == len(keep_mask):
                    properties[key] = properties[key][keep_mask]
        
        # Filter by width
        if 'widths' in properties:
            widths = properties['widths']
            passing_peaks = [p_idx for i, p_idx in enumerate(peaks) if widths[i] >= width_samples]
            peaks_passing_width = np.array(passing_peaks)
        else:
            peaks_passing_width = peaks
        
        # Filter by baseline
        if len(peaks_passing_width) > 0:
            peak_amps = amplitudes[peaks_passing_width]
            good_peaks = np.array([p_idx for i, p_idx in enumerate(peaks_passing_width) 
                                   if peak_amps[i] > baseline_high])
        else:
            good_peaks = peaks_passing_width
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=good_peaks,
            all_peaks=peaks,
            properties=properties
        )
    
    def _analyze_single_waveform(
        self,
        wf_file: Path,
        prominence: float,
        width_samples: int,
        min_dist_samples: int,
        baseline_high: float,
        max_dist_low: float,
        max_dist_high: float
    ) -> WaveformResult:
        """Analyze a single waveform file."""
        t_half, amplitudes = self.waveform_data.read_waveform_file(wf_file)
        
        # Find peaks
        peaks, properties = find_peaks(
            amplitudes,
            height=0.0,
            prominence=prominence,
            width=0,
            distance=min_dist_samples
        )
        
        # Handle saturation - merge multiple saturated peaks
        peaks, properties = self._handle_saturation(peaks, properties, amplitudes)
        
        # Filter by width
        peaks_passing_width = self._filter_by_width(peaks, properties, width_samples)
        
        # Filter by baseline
        good_peaks = self._filter_by_baseline(peaks_passing_width, amplitudes, baseline_high)
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=good_peaks,
            all_peaks=peaks,
            properties=properties
        )
    
    def _handle_saturation(
        self,
        peaks: np.ndarray,
        properties: dict,
        amplitudes: np.ndarray
    ) -> Tuple[np.ndarray, dict]:
        """Handle saturation by merging multiple saturated peaks."""
        if len(peaks) <= 1:
            return peaks, properties
        
        saturation_threshold = self.waveform_data.global_max_amp * 0.95
        peak_amps = amplitudes[peaks]
        saturated_mask = peak_amps >= saturation_threshold
        
        if np.sum(saturated_mask) > 1:
            # Multiple saturated peaks - keep only the highest one
            saturated_indices = np.where(saturated_mask)[0]
            max_sat_peak_idx = saturated_indices[np.argmax(peak_amps[saturated_indices])]
            
            # Create mask for peaks to keep
            keep_mask = ~saturated_mask
            keep_mask[max_sat_peak_idx] = True
            
            # Filter peaks and properties
            peaks = peaks[keep_mask]
            for key in properties:
                if isinstance(properties[key], np.ndarray) and len(properties[key]) == len(keep_mask):
                    properties[key] = properties[key][keep_mask]
        
        return peaks, properties
    
    def _filter_by_width(
        self,
        peaks: np.ndarray,
        properties: dict,
        width_samples: int
    ) -> np.ndarray:
        """Filter peaks by minimum width."""
        if 'widths' not in properties:
            return peaks
        
        widths = properties['widths']
        passing_peaks = []
        
        for i, p_idx in enumerate(peaks):
            if widths[i] >= width_samples:
                passing_peaks.append(p_idx)
        
        return np.array(passing_peaks)
    
    def _filter_by_baseline(
        self,
        peaks: np.ndarray,
        amplitudes: np.ndarray,
        baseline_high: float
    ) -> np.ndarray:
        """Filter peaks that are above baseline."""
        if len(peaks) == 0:
            return peaks
        
        peak_amps = amplitudes[peaks]
        good_peaks = []
        
        for i, p_idx in enumerate(peaks):
            if peak_amps[i] > baseline_high:
                good_peaks.append(p_idx)
        
        return np.array(good_peaks)
    
    def _find_main_candidates(
        self,
        good_peaks: np.ndarray,
        amplitudes: np.ndarray,
        max_dist_low: float,
        max_dist_high: float
    ) -> List[int]:
        """Find peaks that fall within the max dist zone."""
        main_candidates = []
        
        for p_idx in good_peaks:
            t = (p_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
            if max_dist_low <= t <= max_dist_high:
                main_candidates.append(p_idx)
        
        return main_candidates
