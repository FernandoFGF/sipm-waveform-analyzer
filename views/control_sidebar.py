"""
Control sidebar for parameter adjustment.
"""
import customtkinter as ctk
from typing import Callable

from config import (
    DEFAULT_PROMINENCE_PCT, DEFAULT_WIDTH_TIME, DEFAULT_MIN_DIST_TIME,
    DEFAULT_BASELINE_PCT, DEFAULT_MAX_DIST_PCT, DEFAULT_AFTERPULSE_PCT
)


class ControlSidebar(ctk.CTkFrame):
    """Sidebar with parameter controls."""
    
    def __init__(
        self, 
        parent,
        on_update_analysis: Callable,
        on_show_temporal_dist: Callable,
        on_show_all_waveforms: Callable
    ):
        """
        Initialize control sidebar.
        
        Args:
            parent: Parent widget
            on_update_analysis: Callback for update button
            on_show_temporal_dist: Callback for temporal distribution button
            on_show_all_waveforms: Callback for all waveforms button
        """
        super().__init__(parent, width=250, corner_radius=0)
        
        self.on_update_analysis = on_update_analysis
        self.on_show_temporal_dist = on_show_temporal_dist
        self.on_show_all_waveforms = on_show_all_waveforms
        
        self.grid_rowconfigure(20, weight=1)
        
        # Logo
        logo_label = ctk.CTkLabel(
            self, 
            text="Peak Finder", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Create parameter controls
        self._create_parameter_controls()
        
        # Update button
        self.btn_update = ctk.CTkButton(
            self, 
            text="Actualizar Búsqueda", 
            command=self.on_update_analysis
        )
        self.btn_update.grid(row=13, column=0, padx=20, pady=(20, 10))
        
        # Temporal distribution button
        self.btn_timedist = ctk.CTkButton(
            self, 
            text="Ver Dist. Temporal", 
            command=self.on_show_temporal_dist,
            fg_color="gray"
        )
        self.btn_timedist.grid(row=14, column=0, padx=20, pady=(0, 10))
        
        # All waveforms button
        self.btn_allwaveforms = ctk.CTkButton(
            self, 
            text="Ver Todas Waveforms", 
            command=self.on_show_all_waveforms,
            fg_color="gray"
        )
        self.btn_allwaveforms.grid(row=15, column=0, padx=20, pady=(0, 20))
        
        # Stats label
        self.stats_label = ctk.CTkLabel(self, text="Cargando...", justify="left")
        self.stats_label.grid(row=16, column=0, padx=20, pady=10, sticky="w")
    
    def _create_parameter_controls(self):
        """Create all parameter control widgets."""
        # Prominence
        self.lbl_prom = ctk.CTkLabel(
            self, 
            text=f"Prominencia: {DEFAULT_PROMINENCE_PCT:.1f}%"
        )
        self.lbl_prom.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.slider_prom = ctk.CTkSlider(
            self, 
            from_=0.1, 
            to=5.0, 
            number_of_steps=49,
            command=self._update_prom_label
        )
        self.slider_prom.set(DEFAULT_PROMINENCE_PCT)
        self.slider_prom.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Width
        self.lbl_width = ctk.CTkLabel(self, text="Anchura Mínima (µs):")
        self.lbl_width.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_width = ctk.CTkEntry(self)
        self.entry_width.insert(0, str(DEFAULT_WIDTH_TIME * 1e6))
        self.entry_width.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Baseline %
        self.lbl_baseline = ctk.CTkLabel(self, text="Baseline (%):")
        self.lbl_baseline.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_baseline = ctk.CTkEntry(self)
        self.entry_baseline.insert(0, str(DEFAULT_BASELINE_PCT))
        self.entry_baseline.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Max Dist %
        self.lbl_maxdist = ctk.CTkLabel(self, text="Zona de Maximos (%):")
        self.lbl_maxdist.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_maxdist = ctk.CTkEntry(self)
        self.entry_maxdist.insert(0, str(DEFAULT_MAX_DIST_PCT))
        self.entry_maxdist.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Afterpulse %
        self.lbl_afterpulse = ctk.CTkLabel(self, text="Afterpulse (%):")
        self.lbl_afterpulse.grid(row=9, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_afterpulse = ctk.CTkEntry(self)
        self.entry_afterpulse.insert(0, str(DEFAULT_AFTERPULSE_PCT))
        self.entry_afterpulse.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Min Distance
        self.lbl_mindist = ctk.CTkLabel(self, text="Dist. Min. (µs):")
        self.lbl_mindist.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.entry_mindist = ctk.CTkEntry(self)
        self.entry_mindist.insert(0, str(DEFAULT_MIN_DIST_TIME * 1e6))
        self.entry_mindist.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")
    
    def _update_prom_label(self, value):
        """Update prominence label when slider changes."""
        self.lbl_prom.configure(text=f"Prominencia: {value:.1f}%")
    
    def get_parameters(self) -> dict:
        """
        Get current parameter values.
        
        Returns:
            Dictionary of parameter values
        """
        try:
            return {
                'prominence_pct': self.slider_prom.get(),
                'width_time': float(self.entry_width.get()) * 1e-6,
                'min_dist_time': float(self.entry_mindist.get()) * 1e-6,
                'baseline_pct': float(self.entry_baseline.get()),
                'max_dist_pct': float(self.entry_maxdist.get()),
                'afterpulse_pct': float(self.entry_afterpulse.get())
            }
        except ValueError:
            # Return defaults on error
            return {
                'prominence_pct': DEFAULT_PROMINENCE_PCT,
                'width_time': DEFAULT_WIDTH_TIME,
                'min_dist_time': DEFAULT_MIN_DIST_TIME,
                'baseline_pct': DEFAULT_BASELINE_PCT,
                'max_dist_pct': DEFAULT_MAX_DIST_PCT,
                'afterpulse_pct': DEFAULT_AFTERPULSE_PCT
            }
    
    def update_stats(self, total_files: int, accepted: int, afterpulse: int, 
                    rejected: int, rejected_ap: int, total_peaks: int):
        """Update statistics display."""
        text = f"Total Archivos: {total_files}\n"
        text += f"Aceptados (1): {accepted}\n"
        text += f"Afterpulses (>1): {afterpulse}\n"
        text += f"Rechazados (0): {rejected}\n"
        text += f"Rech. c/ AP (>1 raw): {rejected_ap}\n"
        text += f"Total Picos: {total_peaks}"
        self.stats_label.configure(text=text)
