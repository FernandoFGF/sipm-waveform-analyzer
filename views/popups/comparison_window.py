"""
Comparison window for comparing two datasets side by side.
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pathlib import Path
from tkinter import filedialog

from utils import read_data_config


class ComparisonWindow(ctk.CTkToplevel):
    """Window for comparing two datasets with waveform visualization."""
    
    def __init__(self, parent, current_controller, current_data_dir):
        """Initialize comparison window."""
        super().__init__(parent)
        
        self.title("Comparador de Datasets")
        self.geometry("1600x1000")
        
        # Make window stay on top and grab focus
        self.transient(parent)
        self.grab_set()
        
        # Store controllers and data
        self.controller1 = current_controller
        self.data_dir1 = current_data_dir
        self.controller2 = None
        self.data_dir2 = None
        
        # Current indices for waveform navigation
        self.current_idx1 = 0
        self.current_idx2 = 0
        self.current_category = "accepted"
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Stats
        self.grid_rowconfigure(2, weight=1)  # Waveforms
        self.grid_rowconfigure(3, weight=0)  # Navigation
        
        # Create UI
        self._create_header()
        self._create_stats_section()
        self._create_waveform_area()
        self._create_navigation()
        
        # Update display
        self._update_display()
        self.focus()
    
    def _create_header(self):
        """Create header with dataset selectors."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Dataset 1
        ds1_frame = ctk.CTkFrame(header_frame)
        ds1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(ds1_frame, text="📊 Dataset 1", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        self.dataset1_label = ctk.CTkLabel(ds1_frame, text=self.data_dir1.name, font=ctk.CTkFont(size=12))
        self.dataset1_label.pack(pady=5)
        
        # Dataset 2
        ds2_frame = ctk.CTkFrame(header_frame)
        ds2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(ds2_frame, text="📊 Dataset 2", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        self.dataset2_label = ctk.CTkLabel(ds2_frame, text="No seleccionado", font=ctk.CTkFont(size=12), text_color="gray")
        self.dataset2_label.pack(pady=5)
        
        self.btn_select_dataset2 = ctk.CTkButton(
            ds2_frame, text="Seleccionar Dataset 2",
            command=self._select_dataset2,
            fg_color="#3498db", hover_color="#2980b9"
        )
        self.btn_select_dataset2.pack(pady=5)
    
    def _create_stats_section(self):
        """Create compact statistics comparison."""
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Configure grid for 3 columns of stats
        for i in range(6):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Create stat labels
        self.stat_labels = {}
        metrics = ["Aceptados", "Rechazados", "Afterpulses", "Total Picos", "Baseline (mV)", "Total Archivos"]
        
        for idx, metric in enumerate(metrics):
            col = idx
            
            # Metric name
            ctk.CTkLabel(stats_frame, text=metric, font=ctk.CTkFont(size=10, weight="bold")).grid(
                row=0, column=col, padx=5, pady=2
            )
            
            # DS1 value
            label1 = ctk.CTkLabel(stats_frame, text="-", font=ctk.CTkFont(size=10), text_color="#3498db")
            label1.grid(row=1, column=col, padx=5, pady=2)
            
            # DS2 value
            label2 = ctk.CTkLabel(stats_frame, text="-", font=ctk.CTkFont(size=10), text_color="#e74c3c")
            label2.grid(row=2, column=col, padx=5, pady=2)
            
            self.stat_labels[metric] = {'ds1': label1, 'ds2': label2}
    
    def _create_waveform_area(self):
        """Create waveform comparison plots."""
        wf_frame = ctk.CTkFrame(self)
        wf_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        wf_frame.grid_columnconfigure(0, weight=1)
        wf_frame.grid_columnconfigure(1, weight=1)
        wf_frame.grid_rowconfigure(0, weight=1)
        
        # Dataset 1 waveform
        self.fig1 = plt.Figure(figsize=(7, 5), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.fig1.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=wf_frame)
        self.canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Dataset 2 waveform
        self.fig2 = plt.Figure(figsize=(7, 5), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
        self.fig2.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=wf_frame)
        self.canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    def _create_navigation(self):
        """Create navigation controls."""
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        # Category selector
        ctk.CTkLabel(nav_frame, text="Categoría:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        self.category_var = ctk.StringVar(value="accepted")
        category_menu = ctk.CTkOptionMenu(
            nav_frame,
            values=["Aceptados", "Rechazados", "Afterpulses"],
            command=self._on_category_change,
            variable=self.category_var
        )
        category_menu.pack(side="left", padx=5)
        
        # Navigation buttons
        ctk.CTkButton(nav_frame, text="← Anterior", command=self._prev_waveform, width=100).pack(side="left", padx=5)
        ctk.CTkButton(nav_frame, text="Siguiente →", command=self._next_waveform, width=100).pack(side="left", padx=5)
        
        # Info label
        self.info_label = ctk.CTkLabel(nav_frame, text="", font=ctk.CTkFont(size=11))
        self.info_label.pack(side="left", padx=20)
    
    def _select_dataset2(self):
        """Select second dataset."""
        from controllers.analysis_controller import AnalysisController
        
        selected_dir = filedialog.askdirectory(
            title="Seleccionar Dataset 2",
            initialdir=str(self.data_dir1.parent)
        )
        
        if not selected_dir:
            return
        
        self.data_dir2 = Path(selected_dir)
        
        # Load config
        import config
        data_config = read_data_config(self.data_dir2)
        
        if data_config:
            old_window_time = config.WINDOW_TIME
            old_trigger = config.TRIGGER_VOLTAGE
            old_num_points = config.NUM_POINTS
            old_sample_time = config.SAMPLE_TIME
            
            if 'window_time' in data_config:
                config.WINDOW_TIME = data_config['window_time']
            if 'trigger_voltage' in data_config:
                config.TRIGGER_VOLTAGE = data_config['trigger_voltage']
            if 'num_points' in data_config:
                config.NUM_POINTS = data_config['num_points']
                config.SAMPLE_TIME = config.WINDOW_TIME / config.NUM_POINTS
        
        # Create controller
        self.controller2 = AnalysisController(data_dir=self.data_dir2)
        self.controller2.load_data()
        
        params = {
            'prominence_pct': 2.0,
            'width_time': 0.2e-6,
            'min_dist_time': 0.05e-6,
            'baseline_pct': 85.0,
            'max_dist_pct': 99.0,
            'afterpulse_pct': 80.0
        }
        self.controller2.run_analysis(**params)
        
        # Restore config
        if data_config:
            config.WINDOW_TIME = old_window_time
            config.TRIGGER_VOLTAGE = old_trigger
            config.NUM_POINTS = old_num_points
            config.SAMPLE_TIME = old_sample_time
        
        self.dataset2_label.configure(text=self.data_dir2.name, text_color="white")
        self.current_idx2 = 0
        self._update_display()
    
    def _on_category_change(self, choice):
        """Handle category change."""
        category_map = {"Aceptados": "accepted", "Rechazados": "rejected", "Afterpulses": "afterpulse"}
        self.current_category = category_map[choice]
        self.current_idx1 = 0
        self.current_idx2 = 0
        self._update_display()
    
    def _next_waveform(self):
        """Navigate to next waveform."""
        results1 = self.controller1.get_results_for_category(self.current_category)
        if results1 and self.current_idx1 < len(results1) - 1:
            self.current_idx1 += 1
        
        if self.controller2:
            results2 = self.controller2.get_results_for_category(self.current_category)
            if results2 and self.current_idx2 < len(results2) - 1:
                self.current_idx2 += 1
        
        self._update_waveforms()
    
    def _prev_waveform(self):
        """Navigate to previous waveform."""
        if self.current_idx1 > 0:
            self.current_idx1 -= 1
        
        if self.controller2 and self.current_idx2 > 0:
            self.current_idx2 -= 1
        
        self._update_waveforms()
    
    def _update_display(self):
        """Update all displays."""
        self._update_statistics()
        self._update_waveforms()
    
    def _update_statistics(self):
        """Update statistics."""
        results1 = self.controller1.results
        
        stats1 = {
            "Aceptados": results1.get_accepted_count(),
            "Rechazados": results1.get_rejected_count(),
            "Afterpulses": results1.get_afterpulse_count(),
            "Total Picos": results1.total_peaks,
            "Baseline (mV)": (results1.baseline_high - results1.baseline_low) * 1000,
            "Total Archivos": self.controller1.waveform_data.get_file_count()
        }
        
        for metric, value in stats1.items():
            if metric == "Baseline (mV)":
                self.stat_labels[metric]['ds1'].configure(text=f"{value:.2f}")
            else:
                self.stat_labels[metric]['ds1'].configure(text=str(value))
        
        if self.controller2:
            results2 = self.controller2.results
            stats2 = {
                "Aceptados": results2.get_accepted_count(),
                "Rechazados": results2.get_rejected_count(),
                "Afterpulses": results2.get_afterpulse_count(),
                "Total Picos": results2.total_peaks,
                "Baseline (mV)": (results2.baseline_high - results2.baseline_low) * 1000,
                "Total Archivos": self.controller2.waveform_data.get_file_count()
            }
            
            for metric, value in stats2.items():
                if metric == "Baseline (mV)":
                    self.stat_labels[metric]['ds2'].configure(text=f"{value:.2f}")
                else:
                    self.stat_labels[metric]['ds2'].configure(text=str(value))
    
    def _update_waveforms(self):
        """Update waveform plots."""
        from config import WINDOW_TIME, SAMPLE_TIME
        
        # Clear plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Plot dataset 1
        results1 = self.controller1.get_results_for_category(self.current_category)
        if results1:
            result1 = results1[self.current_idx1]
            t_axis = (np.arange(len(result1.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
            
            self.ax1.plot(t_axis, result1.amplitudes * 1000, color='#3498db', linewidth=1)
            
            # Convert peaks to int for indexing
            peak_indices = result1.peaks.astype(int) if hasattr(result1.peaks, 'astype') else np.array(result1.peaks, dtype=int)
            self.ax1.plot(t_axis[peak_indices], result1.amplitudes[peak_indices] * 1000, 
                         'o', color='white', markeredgecolor='black', markersize=6)
            
            self.ax1.set_title(f"DS1: {result1.filename} ({len(result1.peaks)} picos)", fontsize=10)
            self.ax1.set_xlabel("Tiempo (µs)", fontsize=9)
            self.ax1.set_ylabel("Amplitud (mV)", fontsize=9)
            self.ax1.grid(True, alpha=0.3)
        
        # Plot dataset 2
        if self.controller2:
            results2 = self.controller2.get_results_for_category(self.current_category)
            if results2:
                result2 = results2[self.current_idx2]
                t_axis = (np.arange(len(result2.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
                
                self.ax2.plot(t_axis, result2.amplitudes * 1000, color='#e74c3c', linewidth=1)
                
                # Convert peaks to int for indexing
                peak_indices = result2.peaks.astype(int) if hasattr(result2.peaks, 'astype') else np.array(result2.peaks, dtype=int)
                self.ax2.plot(t_axis[peak_indices], result2.amplitudes[peak_indices] * 1000,
                             'o', color='white', markeredgecolor='black', markersize=6)
                
                self.ax2.set_title(f"DS2: {result2.filename} ({len(result2.peaks)} picos)", fontsize=10)
                self.ax2.set_xlabel("Tiempo (µs)", fontsize=9)
                self.ax2.set_ylabel("Amplitud (mV)", fontsize=9)
                self.ax2.grid(True, alpha=0.3)
        
        self.canvas1.draw()
        self.canvas2.draw()
        
        # Update info
        if results1:
            total1 = len(results1)
            info_text = f"DS1: {self.current_idx1 + 1}/{total1}"
            
            if self.controller2:
                results2 = self.controller2.get_results_for_category(self.current_category)
                if results2:
                    total2 = len(results2)
                    info_text += f"  |  DS2: {self.current_idx2 + 1}/{total2}"
            
            self.info_label.configure(text=info_text)


def show_comparison_window(parent, controller, data_dir):
    """Show comparison window."""
    window = ComparisonWindow(parent, controller, data_dir)
    window.focus()
