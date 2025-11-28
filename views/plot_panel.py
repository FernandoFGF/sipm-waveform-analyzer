"""
Reusable plot panel component for displaying waveforms.
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import WINDOW_TIME, SAMPLE_TIME, COLOR_ACCEPTED, COLOR_REJECTED, COLOR_AFTERPULSE, COLOR_REJECTED_AFTERPULSE
from models.analysis_results import WaveformResult


class PlotPanel(ctk.CTkFrame):
    """Reusable panel for displaying waveform plots."""
    
    def __init__(self, parent, title: str, color: str, on_next, on_prev):
        """
        Initialize plot panel.
        
        Args:
            parent: Parent widget
            title: Panel title
            color: Line color for waveforms
            on_next: Callback for next button
            on_prev: Callback for previous button
        """
        super().__init__(parent)
        
        self.title_text = title
        self.color = color
        self.on_next = on_next
        self.on_prev = on_prev
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create title
        self.title_label = ctk.CTkLabel(
            self, 
            text=title, 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.grid(row=1, column=0, pady=2)
        
        # Create plot area
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create navigation controls
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=2, column=0, pady=10)
        
        btn_prev = ctk.CTkButton(
            nav_frame, 
            text="← Anterior", 
            width=100,
            command=self.on_prev
        )
        btn_prev.pack(side="left", padx=5)
        
        btn_next = ctk.CTkButton(
            nav_frame, 
            text="Siguiente →", 
            width=100,
            command=self.on_next
        )
        btn_next.pack(side="left", padx=5)
    
    def update_plot(
        self,
        result: WaveformResult,
        global_min_amp: float,
        global_max_amp: float,
        baseline_low: float,
        baseline_high: float,
        max_dist_low: float,
        max_dist_high: float,
        afterpulse_low: float = 0,
        afterpulse_high: float = 0,
        show_afterpulse_zone: bool = False
    ):
        """
        Update plot with new waveform data.
        
        Args:
            result: WaveformResult to display
            global_min_amp: Global minimum amplitude
            global_max_amp: Global maximum amplitude
            baseline_low: Baseline lower bound
            baseline_high: Baseline upper bound
            max_dist_low: Max dist zone lower bound
            max_dist_high: Max dist zone upper bound
            afterpulse_low: Afterpulse zone lower bound
            afterpulse_high: Afterpulse zone upper bound
            show_afterpulse_zone: Whether to show afterpulse zone
        """
        self.ax.clear()
        
        amplitudes = result.amplitudes
        valid_peaks = result.peaks
        all_peaks = result.all_peaks
        
        # Time axis (relative to center/trigger)
        t_axis = (np.arange(len(amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
        
        # Plot waveform
        self.ax.plot(t_axis, amplitudes * 1000, color=self.color, linewidth=1, label='Signal')
        
        # Plot baseline area
        self.ax.axhspan(baseline_low * 1000, baseline_high * 1000, 
                       color='yellow', alpha=0.2, label='Baseline')
        
        # Plot max dist area
        self.ax.axvspan(max_dist_low * 1e6, max_dist_high * 1e6, 
                       color='blue', alpha=0.15, label='Zona de Maximos')
        
        # Plot afterpulse area (only in afterpulse plots)
        if show_afterpulse_zone and (afterpulse_low != 0 or afterpulse_high != 0):
            self.ax.axvspan(afterpulse_low * 1e6, afterpulse_high * 1e6, 
                           color='green', alpha=0.15, label='Afterpulse')
        
        # Plot rejected peaks (in all_peaks but not in valid_peaks)
        rejected_peaks = [p for p in all_peaks if p not in valid_peaks]
        if len(rejected_peaks) > 0:
            self.ax.plot(t_axis[rejected_peaks], amplitudes[rejected_peaks] * 1000, 'x',
                        color='red', markeredgecolor='darkred', markersize=8, 
                        markeredgewidth=2, label='Rechazados')
        
        # Plot valid peaks
        if len(valid_peaks) > 0:
            self.ax.plot(t_axis[valid_peaks], amplitudes[valid_peaks] * 1000, 'o',
                        color='white', markeredgecolor='black', markersize=6, label='Válidos')
        
        self.ax.set_title(
            f"{result.filename} - {len(valid_peaks)} Picos Válidos ({len(all_peaks)} Detectados)",
            fontsize=10
        )
        self.ax.set_xlabel("Tiempo (µs)", fontsize=8)
        self.ax.set_ylabel("Amplitud (mV)", fontsize=8)
        self.ax.set_ylim(global_min_amp * 1000, global_max_amp * 1000)
        self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def show_no_data(self):
        """Display 'no data' message."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No hay datos", ha='center', va='center')
        self.canvas.draw()
    
    def update_title(self, title: str):
        """Update panel title."""
        self.title_label.configure(text=title)
