"""
Export utilities for analysis results.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

from models.analysis_results import AnalysisResults, WaveformResult
from models.signal_processing import SiPMMetrics
from config import SAMPLE_TIME, WINDOW_TIME


class ResultsExporter:
    """Export analysis results to various formats."""
    
    @staticmethod
    def export_analysis_to_csv(results: AnalysisResults, filepath: str):
        """
        Export analysis results to CSV file.
        
        Args:
            results: AnalysisResults object
            filepath: Output CSV file path
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'filename',
                'category',
                'num_peaks',
                'num_all_peaks',
                'max_amplitude_mV',
                'peak_times_us',
                'peak_amplitudes_mV'
            ])
            
            # Write accepted results
            for res in results.accepted_results:
                ResultsExporter._write_waveform_row(writer, res, 'accepted')
            
            # Write afterpulse results
            for res in results.afterpulse_results:
                ResultsExporter._write_waveform_row(writer, res, 'afterpulse')
            
            # Write rejected results
            for res in results.rejected_results:
                ResultsExporter._write_waveform_row(writer, res, 'rejected')
            
            # Write rejected afterpulse results
            for res in results.rejected_afterpulse_results:
                ResultsExporter._write_waveform_row(writer, res, 'rejected_afterpulse')
        
        print(f"[OK] Analysis exported to {filepath}")
    
    @staticmethod
    def _write_waveform_row(writer, res: WaveformResult, category: str):
        """Write a single waveform result row to CSV."""
        # Calculate peak times relative to trigger
        peak_times_us = [(idx * SAMPLE_TIME - WINDOW_TIME/2) * 1e6 for idx in res.peaks]
        peak_amps_mV = [res.amplitudes[idx] * 1000 for idx in res.peaks]
        
        max_amp_mV = max(peak_amps_mV) if peak_amps_mV else 0.0
        
        writer.writerow([
            res.filename,
            category,
            len(res.peaks),
            len(res.all_peaks),
            f"{max_amp_mV:.2f}",
            ';'.join([f"{t:.3f}" for t in peak_times_us]),
            ';'.join([f"{a:.2f}" for a in peak_amps_mV])
        ])
    
    @staticmethod
    def export_analysis_to_json(results: AnalysisResults, filepath: str, params: Dict[str, Any] = None):
        """
        Export analysis results to JSON file.
        
        Args:
            results: AnalysisResults object
            filepath: Output JSON file path
            params: Optional analysis parameters to include
        """
        data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'parameters': params if params else {},
            'statistics': {
                'total_files': (len(results.accepted_results) + 
                               len(results.afterpulse_results) +
                               len(results.rejected_results) +
                               len(results.rejected_afterpulse_results)),
                'accepted_count': len(results.accepted_results),
                'afterpulse_count': len(results.afterpulse_results),
                'rejected_count': len(results.rejected_results),
                'rejected_afterpulse_count': len(results.rejected_afterpulse_results),
                'total_peaks': results.total_peaks,
                'baseline_low_mV': results.baseline_low * 1000,
                'baseline_high_mV': results.baseline_high * 1000,
                'max_dist_low_us': results.max_dist_low * 1e6,
                'max_dist_high_us': results.max_dist_high * 1e6
                # Note: afterpulse zone removed
            },
            'waveforms': {
                'accepted': [ResultsExporter._waveform_to_dict(r) for r in results.accepted_results],
                'afterpulse': [ResultsExporter._waveform_to_dict(r) for r in results.afterpulse_results],
                'rejected': [ResultsExporter._waveform_to_dict(r) for r in results.rejected_results],
                'rejected_afterpulse': [ResultsExporter._waveform_to_dict(r) for r in results.rejected_afterpulse_results]
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] Analysis exported to {filepath}")
    
    @staticmethod
    def _waveform_to_dict(res: WaveformResult) -> Dict[str, Any]:
        """Convert WaveformResult to dictionary."""
        peak_times_us = [(idx * SAMPLE_TIME - WINDOW_TIME/2) * 1e6 for idx in res.peaks]
        peak_amps_mV = [res.amplitudes[idx] * 1000 for idx in res.peaks]
        
        return {
            'filename': res.filename,
            'num_peaks': len(res.peaks),
            'num_all_peaks': len(res.all_peaks),
            'peak_times_us': [round(t, 3) for t in peak_times_us],
            'peak_amplitudes_mV': [round(a, 2) for a in peak_amps_mV],
            'max_amplitude_mV': round(max(peak_amps_mV), 2) if peak_amps_mV else 0.0
        }
    
    @staticmethod
    def export_sipm_metrics_to_csv(metrics: SiPMMetrics, filepath: str, 
                                    amplitude_threshold: float = None, 
                                    time_threshold: float = None):
        """
        Export SiPM metrics to CSV file.
        
        Args:
            metrics: SiPMMetrics object
            filepath: Output CSV file path
            amplitude_threshold: Amplitude threshold used (mV)
            time_threshold: Time threshold used (us)
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Metric', 'Value', 'Unit'])
            
            # Thresholds
            if amplitude_threshold is not None:
                writer.writerow(['Amplitude Threshold', f"{amplitude_threshold:.1f}", 'mV'])
            if time_threshold is not None:
                writer.writerow(['Time Threshold', f"{time_threshold:.1f}", 'µs'])
            
            writer.writerow([])  # Empty row
            
            # Event counts
            writer.writerow(['Total Events', metrics.total_events, 'count'])
            writer.writerow(['DCR Events', metrics.dcr_count, 'count'])
            writer.writerow(['Crosstalk Events', metrics.crosstalk_count, 'count'])
            writer.writerow(['Afterpulse Events', metrics.afterpulse_count, 'count'])
            writer.writerow(['Crosstalk+Afterpulse Events', metrics.crosstalk_afterpulse_count, 'count'])
            
            writer.writerow([])  # Empty row
            
            # Percentages
            writer.writerow(['Crosstalk', f"{metrics.crosstalk_pct:.2f}", '%'])
            writer.writerow(['Afterpulse', f"{metrics.afterpulse_pct:.2f}", '%'])
            writer.writerow(['Crosstalk+Afterpulse', f"{metrics.crosstalk_afterpulse_pct:.2f}", '%'])
            
            writer.writerow([])  # Empty row
            
            # DCR rates
            writer.writerow(['DCR Rate (Method 1: events/time)', f"{metrics.dcr_rate_total_hz:.2f}", 'Hz'])
            writer.writerow(['DCR Rate (Method 2: 1/mean_interval)', f"{metrics.dcr_rate_avg_hz:.2f}", 'Hz'])
        
        print(f"[OK] SiPM metrics exported to {filepath}")
    
    @staticmethod
    def export_sipm_metrics_to_json(metrics: SiPMMetrics, filepath: str,
                                     amplitude_threshold: float = None,
                                     time_threshold: float = None):
        """
        Export SiPM metrics to JSON file.
        
        Args:
            metrics: SiPMMetrics object
            filepath: Output JSON file path
            amplitude_threshold: Amplitude threshold used (mV)
            time_threshold: Time threshold used (us)
        """
        data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'type': 'sipm_metrics'
            },
            'thresholds': {
                'amplitude_mV': amplitude_threshold,
                'time_us': time_threshold
            },
            'event_counts': {
                'total': metrics.total_events,
                'dcr': metrics.dcr_count,
                'crosstalk': metrics.crosstalk_count,
                'afterpulse': metrics.afterpulse_count,
                'crosstalk_afterpulse': metrics.crosstalk_afterpulse_count
            },
            'percentages': {
                'crosstalk_pct': round(metrics.crosstalk_pct, 2),
                'afterpulse_pct': round(metrics.afterpulse_pct, 2),
                'crosstalk_afterpulse_pct': round(metrics.crosstalk_afterpulse_pct, 2)
            },
            'dcr_rates_hz': {
                'method_1_total_rate': round(metrics.dcr_rate_total_hz, 2),
                'method_2_avg_rate': round(metrics.dcr_rate_avg_hz, 2),
                'difference_pct': round(abs(metrics.dcr_rate_total_hz - metrics.dcr_rate_avg_hz) / 
                                       metrics.dcr_rate_total_hz * 100, 2) if metrics.dcr_rate_total_hz > 0 else 0
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] SiPM metrics exported to {filepath}")
