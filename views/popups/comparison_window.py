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
    """Window for comparing two datasets."""
    
    def __init__(self, parent, current_controller, current_data_dir):
        """
        Initialize comparison window.
        
        Args:
            parent: Parent window
            current_controller: Current analysis controller (Dataset 1)
            current_data_dir: Current data directory path
        """
        super().__init__(parent)
        
        self.title("Comparador de Datasets")
        self.geometry("1400x900")
        
        # Make window stay on top and grab focus
        self.transient(parent)
        self.grab_set()
        
        # Store controllers and data
        self.controller1 = current_controller
        self.data_dir1 = current_data_dir
        self.controller2 = None
        self.data_dir2 = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create header with dataset selectors
        self._create_header()
        
        # Create main comparison area
        self._create_comparison_area()
        
        # Update display with current dataset
        self._update_display()
        
        # Focus the window
        self.focus()
    
    def _create_header(self):
        """Create header with dataset information and controls."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Configure columns
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Dataset 1 info
        dataset1_frame = ctk.CTkFrame(header_frame)
        dataset1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            dataset1_frame,
            text="📊 Dataset 1",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.dataset1_label = ctk.CTkLabel(
            dataset1_frame,
            text=self.data_dir1.name,
            font=ctk.CTkFont(size=12)
        )
        self.dataset1_label.pack(pady=5)
        
        # Dataset 2 info and selector
        dataset2_frame = ctk.CTkFrame(header_frame)
        dataset2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            dataset2_frame,
            text="📊 Dataset 2",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.dataset2_label = ctk.CTkLabel(
            dataset2_frame,
            text="No seleccionado",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.dataset2_label.pack(pady=5)
        
        self.btn_select_dataset2 = ctk.CTkButton(
            dataset2_frame,
            text="Seleccionar Dataset 2",
            command=self._select_dataset2,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.btn_select_dataset2.pack(pady=5)
    
    def _create_comparison_area(self):
        """Create main comparison area with statistics and plots."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=2)
        
        # Statistics comparison table
        self.stats_frame = ctk.CTkFrame(main_frame)
        self.stats_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self._create_stats_table()
        
        # Plots area
        plots_frame = ctk.CTkFrame(main_frame)
        plots_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Configure plots grid
        plots_frame.grid_columnconfigure(0, weight=1)
        plots_frame.grid_columnconfigure(1, weight=1)
        plots_frame.grid_rowconfigure(0, weight=1)
        
        # Create matplotlib figures
        self._create_plots(plots_frame)
    
    def _create_stats_table(self):
        """Create statistics comparison table."""
        # Title
        ctk.CTkLabel(
            self.stats_frame,
            text="Comparación de Estadísticas",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Headers
        headers = ["Métrica", "Dataset 1", "Dataset 2", "Diferencia"]
        for col, header in enumerate(headers):
            ctk.CTkLabel(
                self.stats_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=1, column=col, padx=10, pady=5)
        
        # Store labels for updating
        self.stat_labels = {}
        
        # Metrics to compare
        metrics = [
            "Total Archivos",
            "Aceptados",
            "Rechazados",
            "Afterpulses",
            "Total Picos",
            "Baseline (mV)"
        ]
        
        for row, metric in enumerate(metrics, start=2):
            # Metric name
            ctk.CTkLabel(
                self.stats_frame,
                text=metric,
                font=ctk.CTkFont(size=11)
            ).grid(row=row, column=0, padx=10, pady=3, sticky="w")
            
            # Dataset 1 value
            label1 = ctk.CTkLabel(
                self.stats_frame,
                text="-",
                font=ctk.CTkFont(size=11)
            )
            label1.grid(row=row, column=1, padx=10, pady=3)
            
            # Dataset 2 value
            label2 = ctk.CTkLabel(
                self.stats_frame,
                text="-",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            label2.grid(row=row, column=2, padx=10, pady=3)
            
            # Difference
            label_diff = ctk.CTkLabel(
                self.stats_frame,
                text="-",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            label_diff.grid(row=row, column=3, padx=10, pady=3)
            
            self.stat_labels[metric] = {
                'dataset1': label1,
                'dataset2': label2,
                'diff': label_diff
            }
    
    def _create_plots(self, parent):
        """Create comparison plots."""
        # Left plot: Bar chart comparison
        self.fig_bars = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax_bars = self.fig_bars.add_subplot(111)
        self.fig_bars.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
        
        self.canvas_bars = FigureCanvasTkAgg(self.fig_bars, master=parent)
        self.canvas_bars.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Right plot: Amplitude distribution comparison
        self.fig_dist = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax_dist = self.fig_dist.add_subplot(111)
        self.fig_dist.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
        
        self.canvas_dist = FigureCanvasTkAgg(self.fig_dist, master=parent)
        self.canvas_dist.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    def _select_dataset2(self):
        """Open dialog to select second dataset."""
        # Import here to avoid circular import
        from controllers.analysis_controller import AnalysisController
        
        # Ask user to select directory
        selected_dir = filedialog.askdirectory(
            title="Seleccionar Dataset 2",
            initialdir=str(self.data_dir1.parent)
        )
        
        if not selected_dir:
            return
        
        self.data_dir2 = Path(selected_dir)
        
        # Load configuration from DATA.txt
        import config
        data_config = read_data_config(self.data_dir2)
        
        if data_config:
            # Temporarily update config for loading
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
        
        # Create controller for dataset 2
        self.controller2 = AnalysisController(data_dir=self.data_dir2)
        self.controller2.load_data()
        
        # Run analysis with same parameters as dataset 1
        params = {
            'prominence_pct': 2.0,
            'width_time': 0.2e-6,
            'min_dist_time': 0.05e-6,
            'baseline_pct': 85.0,
            'max_dist_pct': 99.0,
            'afterpulse_pct': 80.0
        }
        self.controller2.run_analysis(**params)
        
        # Restore original config
        if data_config:
            config.WINDOW_TIME = old_window_time
            config.TRIGGER_VOLTAGE = old_trigger
            config.NUM_POINTS = old_num_points
            config.SAMPLE_TIME = old_sample_time
        
        # Update display
        self.dataset2_label.configure(text=self.data_dir2.name, text_color="white")
        self._update_display()
    
    def _update_display(self):
        """Update all statistics and plots."""
        self._update_statistics()
        self._update_plots()
    
    def _update_statistics(self):
        """Update statistics comparison table."""
        # Get stats from dataset 1
        results1 = self.controller1.results
        
        stats1 = {
            "Total Archivos": self.controller1.waveform_data.get_file_count(),
            "Aceptados": results1.get_accepted_count(),
            "Rechazados": results1.get_rejected_count(),
            "Afterpulses": results1.get_afterpulse_count(),
            "Total Picos": results1.total_peaks,
            "Baseline (mV)": (results1.baseline_high - results1.baseline_low) * 1000
        }
        
        # Update dataset 1 labels
        for metric, value in stats1.items():
            if metric == "Baseline (mV)":
                self.stat_labels[metric]['dataset1'].configure(text=f"{value:.2f}")
            else:
                self.stat_labels[metric]['dataset1'].configure(text=str(value))
        
        # Update dataset 2 if available
        if self.controller2:
            results2 = self.controller2.results
            
            stats2 = {
                "Total Archivos": self.controller2.waveform_data.get_file_count(),
                "Aceptados": results2.get_accepted_count(),
                "Rechazados": results2.get_rejected_count(),
                "Afterpulses": results2.get_afterpulse_count(),
                "Total Picos": results2.total_peaks,
                "Baseline (mV)": (results2.baseline_high - results2.baseline_low) * 1000
            }
            
            # Update dataset 2 labels and calculate differences
            for metric in stats1.keys():
                val1 = stats1[metric]
                val2 = stats2[metric]
                
                # Update value
                if metric == "Baseline (mV)":
                    self.stat_labels[metric]['dataset2'].configure(
                        text=f"{val2:.2f}",
                        text_color="white"
                    )
                else:
                    self.stat_labels[metric]['dataset2'].configure(
                        text=str(val2),
                        text_color="white"
                    )
                
                # Calculate difference
                if val1 != 0:
                    diff_pct = ((val2 - val1) / val1) * 100
                    diff_text = f"{diff_pct:+.1f}%"
                    
                    # Color based on difference
                    if abs(diff_pct) < 5:
                        color = "gray"
                    elif diff_pct > 0:
                        color = "#2ecc71"  # Green for positive
                    else:
                        color = "#e74c3c"  # Red for negative
                    
                    self.stat_labels[metric]['diff'].configure(
                        text=diff_text,
                        text_color=color
                    )
                else:
                    self.stat_labels[metric]['diff'].configure(text="N/A")
    
    def _update_plots(self):
        """Update comparison plots."""
        # Clear plots
        self.ax_bars.clear()
        self.ax_dist.clear()
        
        # Bar chart comparison
        categories = ['Aceptados', 'Rechazados', 'Afterpulses']
        
        results1 = self.controller1.results
        values1 = [
            results1.get_accepted_count(),
            results1.get_rejected_count(),
            results1.get_afterpulse_count()
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = self.ax_bars.bar(x - width/2, values1, width, label=self.data_dir1.name, color='#3498db')
        
        if self.controller2:
            results2 = self.controller2.results
            values2 = [
                results2.get_accepted_count(),
                results2.get_rejected_count(),
                results2.get_afterpulse_count()
            ]
            bars2 = self.ax_bars.bar(x + width/2, values2, width, label=self.data_dir2.name, color='#e74c3c')
        
        self.ax_bars.set_xlabel('Categoría')
        self.ax_bars.set_ylabel('Cantidad')
        self.ax_bars.set_title('Comparación de Categorías')
        self.ax_bars.set_xticks(x)
        self.ax_bars.set_xticklabels(categories)
        self.ax_bars.legend()
        self.ax_bars.grid(True, alpha=0.3)
        
        # Amplitude distribution comparison
        if self.controller1.waveform_data.all_amplitudes_flat.size > 0:
            self.ax_dist.hist(
                self.controller1.waveform_data.all_amplitudes_flat * 1000,
                bins=50,
                alpha=0.6,
                label=self.data_dir1.name,
                color='#3498db'
            )
        
        if self.controller2 and self.controller2.waveform_data.all_amplitudes_flat.size > 0:
            self.ax_dist.hist(
                self.controller2.waveform_data.all_amplitudes_flat * 1000,
                bins=50,
                alpha=0.6,
                label=self.data_dir2.name,
                color='#e74c3c'
            )
        
        self.ax_dist.set_xlabel('Amplitud (mV)')
        self.ax_dist.set_ylabel('Frecuencia')
        self.ax_dist.set_title('Distribución de Amplitudes')
        self.ax_dist.legend()
        self.ax_dist.grid(True, alpha=0.3)
        
        # Redraw canvases
        self.canvas_bars.draw()
        self.canvas_dist.draw()


def show_comparison_window(parent, controller, data_dir):
    """
    Show comparison window.
    
    Args:
        parent: Parent window
        controller: Current analysis controller
        data_dir: Current data directory
    """
    window = ComparisonWindow(parent, controller, data_dir)
    window.focus()
