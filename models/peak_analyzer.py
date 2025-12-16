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
from models.baseline_tracker import BaselineTracker
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
        negative_trigger_mv: float
    ) -> AnalysisResults:
        """
        Analyze all waveforms with given parameters.
        Now calculates global statistics during analysis (single-pass).
        
        Args:
            prominence_pct: Prominence threshold as percentage of amplitude range
            width_time: Minimum peak width in seconds
            min_dist_time: Minimum distance between peaks in seconds
            baseline_pct: Baseline percentile range
            max_dist_pct: Max distance zone percentile
            negative_trigger_mv: Negative trigger threshold in mV (reject if any peak below)
            
        Returns:
            AnalysisResults containing classified waveforms
        """
        results = AnalysisResults()
        
        # First pass: Analyze waveforms and collect statistics simultaneously
        num_files = len(self.waveform_data.waveform_files)
        use_parallel = num_files > 50
        
        print(f"Analyzing {num_files} files {'in parallel' if use_parallel else 'sequentially'}...")
        
        # Analyze waveforms (this reads files for the first and only time)
        if use_parallel:
            wf_results = self._analyze_waveforms_parallel_initial(
                prominence_pct,
                width_time,
                min_dist_time
            )
        else:
            wf_results = self._analyze_waveforms_sequential_initial(
                prominence_pct,
                width_time,
                min_dist_time
            )
        
        # Calculate max dist range FIRST to define exclusion zone
        if len(self.waveform_data.all_max_times) > 0:
            low_p = (100 - max_dist_pct) / 2
            high_p = 100 - low_p
            results.max_dist_low = np.percentile(self.waveform_data.all_max_times, low_p)
            results.max_dist_high = np.percentile(self.waveform_data.all_max_times, high_p)
            print(f"Max Dist ({max_dist_pct}%): {results.max_dist_low*1e6:.2f}µs - {results.max_dist_high*1e6:.2f}µs")
        else:
            # Fallback if no peaks found
            results.max_dist_low = -0.1e-6
            results.max_dist_high = 0.1e-6

        # Collect data for baseline calculation (EXCLUDING the Max Dist zone)
        print("Collecting amplitude data for baseline calculation (excluding signal zone)...")
        baseline_data_list = []
        
        # Calculate indices for exclusion zone
        # t = index * SAMPLE_TIME - WINDOW_TIME/2
        # index = (t + WINDOW_TIME/2) / SAMPLE_TIME
        from config import SAMPLE_TIME, WINDOW_TIME
        
        idx_start = int((results.max_dist_low + WINDOW_TIME/2) / SAMPLE_TIME)
        idx_end = int((results.max_dist_high + WINDOW_TIME/2) / SAMPLE_TIME)
        
        print(f"Excluding indices [{idx_start}, {idx_end}] from baseline calculation")
        
        for wf_result in wf_results:
            if wf_result is None:
                continue
            
            arr_len = len(wf_result.amplitudes)
            
            # Clamp indices to valid range
            valid_idx_start = max(0, min(idx_start, arr_len))
            valid_idx_end = max(0, min(idx_end, arr_len))
            
            # Concatenate pre-signal and post-signal regions
            # Region 1: [0, valid_idx_start)
            # Region 2: [valid_idx_end, arr_len)
            
            if valid_idx_start > 0:
                baseline_data_list.append(wf_result.amplitudes[:valid_idx_start])
            
            if valid_idx_end < arr_len:
                baseline_data_list.append(wf_result.amplitudes[valid_idx_end:])
        
        # Store for processing
        if baseline_data_list:
            baseline_amplitudes_flat = np.concatenate(baseline_data_list)
        else:
            baseline_amplitudes_flat = np.array([])
            
        # Also store full for other uses if needed, but critical is baseline calc
        # For simplicity/memory, we might not strictly need 'all_amplitudes_flat' for anything else critical right now
        # except maybe advanced analysis popup? Let's check. 
        # The original code stored self.waveform_data.all_amplitudes_flat.
        # Let's keep storing ALL data as well for compatibility, or just use the filtered one?
        # The user specifically complained about the baseline calculation.
        # "all_amplitudes_flat" implies ALL.
        
        # Construct full list for storage (memory intensive but consistent with previous code)
        all_data_list = [res.amplitudes for res in wf_results if res is not None]
        if all_data_list:
            self.waveform_data.all_amplitudes_flat = np.concatenate(all_data_list)
        
        # Calculate baseline range from FILTERED amplitudes
        if len(baseline_amplitudes_flat) > 0:
            # No need to filter by trigger voltage - we already excluded the signal zone by time
            # The remaining data is pure noise (pre-trigger and post-signal)
            baseline_amplitudes = baseline_amplitudes_flat
            
            if len(baseline_amplitudes) > 0:
                low_p = (100 - baseline_pct) / 2
                high_p = 100 - low_p
                results.baseline_low = np.percentile(baseline_amplitudes, low_p)
                results.baseline_high = np.percentile(baseline_amplitudes, high_p)
                print(f"Baseline ({baseline_pct}%, {len(baseline_amplitudes)} pts outside signal zone): "
                      f"{results.baseline_low*1000:.2f}mV - {results.baseline_high*1000:.2f}mV")
            else:
                print("Warning: No amplitudes in quiet zone")
        
        # Now filter and classify results using calculated thresholds
        from config import SAMPLE_TIME, WINDOW_TIME
        afterpulse_times = []
        negative_trigger_v = negative_trigger_mv / 1000.0  # Convert mV to V
        
        for wf_result in wf_results:
            if wf_result is None:
                continue
            
            
            # Check for perturbation (negative trigger violation)
            # Count downward crossings: if signal crosses down 2+ times, it's perturbation
            has_perturbation = False
            min_amplitude = np.min(wf_result.amplitudes)
            
            if min_amplitude < negative_trigger_v:
                # Detect downward crossings through the threshold
                # A crossing happens when signal goes from above to below threshold
                below_threshold = wf_result.amplitudes < negative_trigger_v
                
                # diff = 1 means transition from above (False) to below (True) = downward crossing
                transitions = np.diff(below_threshold.astype(int))
                downward_crossings = np.sum(transitions == 1)
                
                # Require at least 2 downward crossings to mark as perturbation
                if downward_crossings >= 2:
                    has_perturbation = True
                    # Mark ALL peaks as perturbation
                    for p_idx in wf_result.all_peaks:
                        wf_result.peak_rejection_reasons[p_idx] = (
                            f"Perturbación ({downward_crossings} cruces hacia abajo del trigger negativo, "
                            f"mín: {min_amplitude*1000:.2f}mV)"
                        )
            
            if has_perturbation:
                # Reject entire waveform due to perturbation
                wf_result.peaks = np.array([])  # No valid peaks
                results.rejected_results.append(wf_result)
                continue
            
            # Filter peaks by baseline and track rejections
            good_peaks = []
            for p_idx in wf_result.peaks:
                if wf_result.amplitudes[p_idx] > results.baseline_high:
                    good_peaks.append(p_idx)
                else:
                    # Track rejection reason
                    wf_result.peak_rejection_reasons[p_idx] = (
                        f"Amplitud bajo baseline ({wf_result.amplitudes[p_idx]*1000:.2f}mV ≤ "
                        f"{results.baseline_high*1000:.2f}mV)"
                    )
            
            good_peaks = np.array(good_peaks) if good_peaks else np.array([])
            
            # Update result with filtered peaks
            wf_result.peaks = good_peaks
            
            # Find main candidates (good peaks inside max dist zone)
            main_candidates = self._find_main_candidates(
                good_peaks,
                wf_result.amplitudes,
                results.max_dist_low,
                results.max_dist_high
            )
            
            if len(main_candidates) == 0:
                # Rejected - no valid peaks in max dist zone
                # Track rejection for peaks outside max dist zone
                for p_idx in good_peaks:
                    t_rel = (p_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                    if t_rel < results.max_dist_low or t_rel > results.max_dist_high:
                        wf_result.peak_rejection_reasons[p_idx] = (
                            f"Fuera de zona de máximos ({t_rel*1e6:.2f}µs no en "
                            f"[{results.max_dist_low*1e6:.2f}, {results.max_dist_high*1e6:.2f}]µs)"
                        )
                results.rejected_results.append(wf_result)
            else:
                # Accepted or Afterpulse
                if len(good_peaks) > 1:
                    # Afterpulse - multiple good peaks
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
        
        
        # Note: Afterpulse zone calculation removed - not needed
        # Afterpulse classification (multiple peaks) is still done above
        
        # Calculate and track baseline amplitude from accepted results only
        if len(results.accepted_results) > 0:
            accepted_amplitudes = []
            for wf_result in results.accepted_results:
                accepted_amplitudes.extend(wf_result.amplitudes)
            
            if len(accepted_amplitudes) > 0:
                from config import TRIGGER_VOLTAGE
                accepted_amplitudes = np.array(accepted_amplitudes)
                
                # Filter out points above trigger voltage
                baseline_accepted_amps = accepted_amplitudes[accepted_amplitudes <= TRIGGER_VOLTAGE]
                
                if len(baseline_accepted_amps) > 0:
                    low_p = (100 - baseline_pct) / 2
                    high_p = 100 - low_p
                    baseline_low_accepted = np.percentile(baseline_accepted_amps, low_p)
                    baseline_high_accepted = np.percentile(baseline_accepted_amps, high_p)
                    
                    baseline_amplitude_mv = (baseline_high_accepted - baseline_low_accepted) * 1000
                    
                    # Track baseline for historical comparison
                    tracker = BaselineTracker()
                    tracker.add_baseline(baseline_amplitude_mv)
                    
                    print(f"Baseline amplitude (accepted only, {len(baseline_accepted_amps)} pts): {baseline_amplitude_mv:.2f}mV")
        
        return results
    
    def _analyze_waveforms_sequential_initial(
        self,
        prominence_pct: float,
        width_time: float,
        min_dist_time: float
    ) -> List[WaveformResult]:
        """Analyze waveforms sequentially without pre-calculated thresholds."""
        results = []
        width_samples = int(width_time / SAMPLE_TIME)
        min_dist_samples = int(min_dist_time / SAMPLE_TIME)
        if min_dist_samples < 1:
            min_dist_samples = 1
        
        # Use a rough estimate for prominence (will be refined later)
        # Assume typical range is 0 to 0.1V
        rough_prominence = (prominence_pct / 100.0) * 0.1
        
        for wf_file in self.waveform_data.waveform_files:
            try:
                wf_result = self._analyze_single_waveform_initial(
                    wf_file,
                    rough_prominence,
                    width_samples,
                    min_dist_samples
                )
                results.append(wf_result)
            except (WaveformError, AnalysisError) as e:
                print(f"Error analyzing {wf_file}: {e}")
                results.append(None)
            except Exception as e:
                print(f"Unexpected error analyzing {wf_file}: {e}")
                results.append(None)
        
        return results
    
    def _analyze_waveforms_parallel_initial(
        self,
        prominence_pct: float,
        width_time: float,
        min_dist_time: float
    ) -> List[WaveformResult]:
        """Analyze waveforms in parallel without pre-calculated thresholds."""
        results = []
        num_workers = min(multiprocessing.cpu_count(), 8)
        
        print(f"Using {num_workers} parallel workers...")
        
        width_samples = int(width_time / SAMPLE_TIME)
        min_dist_samples = int(min_dist_time / SAMPLE_TIME)
        if min_dist_samples < 1:
            min_dist_samples = 1
        
        rough_prominence = (prominence_pct / 100.0) * 0.1
        
        args_list = [
            (wf_file, rough_prominence, width_samples, min_dist_samples)
            for wf_file in self.waveform_data.waveform_files
        ]
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_single_waveform_initial_wrapper, args): args[0]
                for args in args_list
            }
            
            completed = 0
            total = len(future_to_file)
            
            for future in as_completed(future_to_file):
                wf_file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error analyzing {wf_file}: {e}")
                    results.append(None)
                
                completed += 1
                if completed % 100 == 0:
                    print(f"Progress: {completed}/{total} files analyzed")
        
        return results
    
    @staticmethod
    def _analyze_single_waveform_initial_wrapper(args):
        """Wrapper for parallel processing (initial pass)."""
        wf_file, prominence, width_samples, min_dist_samples = args
        
        from models.waveform_data import WaveformData
        waveform_data = WaveformData()
        
        t_half, amplitudes = waveform_data.read_waveform_file(wf_file)
        
        # Find peaks with rough prominence
        peaks, properties = find_peaks(
            amplitudes,
            height=0.0,
            prominence=prominence,
            width=0,
            distance=min_dist_samples
        )
        
        # Store ALL detected peaks before filtering (for visualization)
        all_detected_peaks = peaks.copy()
        rejection_reasons = {}
        
        # Filter by width and track rejections
        if 'widths' in properties:
            widths = properties['widths']
            passing_peaks = []
            for i, p_idx in enumerate(peaks):
                if widths[i] >= width_samples:
                    passing_peaks.append(p_idx)
                else:
                    # Track rejection reason
                    rejection_reasons[p_idx] = f"Anchura insuficiente ({widths[i]:.1f} < {width_samples} samples)"
            peaks = np.array(passing_peaks) if passing_peaks else np.array([])
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=peaks,
            all_peaks=all_detected_peaks,  # All peaks including rejected by width
            properties=properties,
            peak_rejection_reasons=rejection_reasons
        )
    
    def _analyze_single_waveform_initial(
        self,
        wf_file: Path,
        prominence: float,
        width_samples: int,
        min_dist_samples: int
    ) -> WaveformResult:
        """Analyze a single waveform without pre-calculated thresholds."""
        t_half, amplitudes = self.waveform_data.read_waveform_file(wf_file)
        
        # Find peaks
        peaks, properties = find_peaks(
            amplitudes,
            height=0.0,
            prominence=prominence,
            width=0,
            distance=min_dist_samples
        )
        
        # Store ALL detected peaks before filtering (for visualization)
        all_detected_peaks = peaks.copy()
        rejection_reasons = {}
        
        # Filter by width and track rejections
        if 'widths' in properties:
            widths = properties['widths']
            passing_peaks = []
            for i, p_idx in enumerate(peaks):
                if widths[i] >= width_samples:
                    passing_peaks.append(p_idx)
                else:
                    # Track rejection reason
                    rejection_reasons[p_idx] = f"Anchura insuficiente ({widths[i]:.1f} < {width_samples} samples)"
            peaks = np.array(passing_peaks) if passing_peaks else np.array([])
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=peaks,
            all_peaks=all_detected_peaks,  # All peaks including rejected by width
            properties=properties,
            peak_rejection_reasons=rejection_reasons
        )
    
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
        from config import SAMPLE_TIME
        waveform_data = WaveformData()
        
        # Dictionary to track rejection reasons
        rejection_reasons = {}
        
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
        original_peaks = peaks.copy()
        global_max_amp = np.max(amplitudes) * 1.05  # Approximate
        saturation_threshold = global_max_amp * 0.95
        peak_amps = amplitudes[peaks]
        saturated_mask = peak_amps >= saturation_threshold
        
        if np.sum(saturated_mask) > 1:
            saturated_indices = np.where(saturated_mask)[0]
            max_sat_peak_idx = saturated_indices[np.argmax(peak_amps[saturated_indices])]
            keep_mask = ~saturated_mask
            keep_mask[max_sat_peak_idx] = True
            
            # Track rejected saturated peaks
            kept_peak_idx = peaks[max_sat_peak_idx]
            for idx in saturated_indices:
                peak_idx = original_peaks[idx]
                if not keep_mask[idx]:
                    rejection_reasons[peak_idx] = "Saturación (pico duplicado fusionado)"
            
            peaks = peaks[keep_mask]
            for key in properties:
                if isinstance(properties[key], np.ndarray) and len(properties[key]) == len(keep_mask):
                    properties[key] = properties[key][keep_mask]
        
        # Filter by width
        peaks_before_width = peaks.copy()
        if 'widths' in properties:
            widths = properties['widths']
            passing_peaks = [p_idx for i, p_idx in enumerate(peaks) if widths[i] >= width_samples]
            peaks_passing_width = np.array(passing_peaks)
            
            # Track peaks rejected by width
            for peak_idx in peaks_before_width:
                if peak_idx not in peaks_passing_width:
                    rejection_reasons[peak_idx] = f"Ancho insuficiente (< {width_samples * SAMPLE_TIME * 1e9:.1f} ns)"
        else:
            peaks_passing_width = peaks
        
        # Filter by baseline
        peaks_before_baseline = peaks_passing_width.copy()
        if len(peaks_passing_width) > 0:
            peak_amps = amplitudes[peaks_passing_width]
            good_peaks = np.array([p_idx for i, p_idx in enumerate(peaks_passing_width) 
                                   if peak_amps[i] > baseline_high])
            
            # Track peaks rejected by baseline
            for peak_idx in peaks_before_baseline:
                if peak_idx not in good_peaks:
                    rejection_reasons[peak_idx] = f"Por debajo del baseline ({baseline_high * 1000:.3f} mV)"
        else:
            good_peaks = peaks_passing_width
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=good_peaks,
            all_peaks=peaks,
            properties=properties,
            peak_rejection_reasons=rejection_reasons
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
        
        # Dictionary to track rejection reasons
        rejection_reasons = {}
        
        # Find peaks
        peaks, properties = find_peaks(
            amplitudes,
            height=0.0,
            prominence=prominence,
            width=0,
            distance=min_dist_samples
        )
        
        # Handle saturation - merge multiple saturated peaks
        original_peaks = peaks.copy()
        peaks, properties = self._handle_saturation(peaks, properties, amplitudes)
        
        # Track saturated peaks that were merged
        if len(original_peaks) != len(peaks):
            saturation_threshold = self.waveform_data.global_max_amp * 0.95
            peak_amps = amplitudes[original_peaks]
            saturated_mask = peak_amps >= saturation_threshold
            saturated_indices = np.where(saturated_mask)[0]
            
            if len(saturated_indices) > 1:
                # Find which saturated peak was kept
                kept_peak_idx = None
                for idx in saturated_indices:
                    if original_peaks[idx] in peaks:
                        kept_peak_idx = original_peaks[idx]
                        break
                
                # Mark rejected saturated peaks
                for idx in saturated_indices:
                    peak_idx = original_peaks[idx]
                    if peak_idx != kept_peak_idx:
                        rejection_reasons[peak_idx] = "Saturación (pico duplicado fusionado)"
        
        # Filter by width
        peaks_before_width = peaks.copy()
        peaks_passing_width = self._filter_by_width(peaks, properties, width_samples)
        
        # Track peaks rejected by width filter
        for peak_idx in peaks_before_width:
            if peak_idx not in peaks_passing_width:
                rejection_reasons[peak_idx] = f"Ancho insuficiente (< {width_samples * SAMPLE_TIME * 1e9:.1f} ns)"
        
        # Filter by baseline
        peaks_before_baseline = peaks_passing_width.copy()
        good_peaks = self._filter_by_baseline(peaks_passing_width, amplitudes, baseline_high)
        
        # Track peaks rejected by baseline filter
        for peak_idx in peaks_before_baseline:
            if peak_idx not in good_peaks:
                rejection_reasons[peak_idx] = f"Por debajo del baseline ({baseline_high * 1000:.3f} mV)"
        
        return WaveformResult(
            filename=wf_file.name,
            t_half=t_half,
            amplitudes=amplitudes,
            peaks=good_peaks,
            all_peaks=peaks,
            properties=properties,
            peak_rejection_reasons=rejection_reasons
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
