"""
Control sidebar for parameter adjustment.
"""
import customtkinter as ctk
from typing import Callable

from config import (
    DEFAULT_PROMINENCE_PCT, DEFAULT_WIDTH_TIME, DEFAULT_MIN_DIST_TIME,
    DEFAULT_BASELINE_PCT, DEFAULT_MAX_DIST_PCT, DEFAULT_AFTERPULSE_PCT
)
from utils import get_config


class ControlSidebar(ctk.CTkFrame):
    """Sidebar with parameter controls."""
    
    def __init__(
        self, 
        parent,
        on_update_analysis: Callable,
        on_show_temporal_dist: Callable,
        on_show_all_waveforms: Callable,
        on_show_charge_histogram: Callable,
        on_export_results: Callable = None,
        on_show_advanced_analysis: Callable = None,
        on_show_signal_processing: Callable = None
    ):
        """
        Initialize control sidebar.
        
        Args:
            parent: Parent widget
            on_update_analysis: Callback for update button
            on_show_temporal_dist: Callback for temporal distribution button
            on_show_all_waveforms: Callback for all waveforms button
            on_show_charge_histogram: Callback for charge histogram button
            on_export_results: Callback for export button
            on_show_advanced_analysis: Callback for advanced SiPM analysis button
            on_show_signal_processing: Callback for signal processing button
        """
        super().__init__(parent, width=250, corner_radius=0)
        
        self.on_update_analysis = on_update_analysis
        self.on_show_temporal_dist = on_show_temporal_dist
        self.on_show_all_waveforms = on_show_all_waveforms
        self.on_show_charge_histogram = on_show_charge_histogram
        self.on_export_results = on_export_results
        self.on_show_advanced_analysis = on_show_advanced_analysis
        self.on_show_signal_processing = on_show_signal_processing
        
        # Get configuration manager
        self.config = get_config()
        
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
        
        # ===== BUTTON GRID SECTION (2x4 Grid) =====
        # Create frame for button grid
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=13, column=0, padx=10, pady=(20, 10), sticky="ew")
        
        # Configure grid columns to be equal width
        button_frame.grid_columnconfigure(0, weight=1, uniform="button")
        button_frame.grid_columnconfigure(1, weight=1, uniform="button")
        
        # Row 1: Actualizar | Guardar conf
        self.btn_update = ctk.CTkButton(
            button_frame,
            text="Actualizar",
            command=self.on_update_analysis,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=110,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.btn_update.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_save_config = ctk.CTkButton(
            button_frame,
            text="Guardar\nconf",
            command=self._save_configuration,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=110,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.btn_save_config.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Row 2: Ver dist. temporal | Ver wf completo
        self.btn_timedist = ctk.CTkButton(
            button_frame,
            text="Ver dist.\ntemporal",
            command=self.on_show_temporal_dist,
            fg_color="gray",
            width=110,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.btn_timedist.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_allwaveforms = ctk.CTkButton(
            button_frame,
            text="Ver wf\ncompleto",
            command=self.on_show_all_waveforms,
            fg_color="gray",
            width=110,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.btn_allwaveforms.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Row 3: Ver hist. carga | Ver análisis avanzado
        self.btn_chargehist = ctk.CTkButton(
            button_frame,
            text="Ver hist.\ncarga",
            command=self.on_show_charge_histogram,
            fg_color="gray",
            width=110,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.btn_chargehist.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        # Advanced analysis button (placeholder for Phase 2)
        self.btn_advanced_analysis = ctk.CTkButton(
            button_frame,
            text="Ver análisis\navanzado",
            command=self.on_show_advanced_analysis if self.on_show_advanced_analysis else lambda: None,
            fg_color="gray",
            width=110,
            height=35,
            font=ctk.CTkFont(size=11),
            state="disabled" if not self.on_show_advanced_analysis else "normal"
        )
        self.btn_advanced_analysis.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Row 4: Filtros | Exportar
        # Signal processing button (placeholder for Phase 3)
        self.btn_signal_processing = ctk.CTkButton(
            button_frame,
            text="Filtros",
            command=self.on_show_signal_processing if self.on_show_signal_processing else lambda: None,
            fg_color="#e67e22",
            hover_color="#d35400",
            width=110,
            height=35,
            font=ctk.CTkFont(size=12),
            state="disabled" if not self.on_show_signal_processing else "normal"
        )
        self.btn_signal_processing.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        # Export results button
        if self.on_export_results:
            self.btn_export = ctk.CTkButton(
                button_frame,
                text="Exportar",
                command=self.on_export_results,
                fg_color="#e67e22",
                hover_color="#d35400",
                width=110,
                height=35,
                font=ctk.CTkFont(size=12)
            )
            self.btn_export.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Stats label (moved below button grid)
        self.stats_label = ctk.CTkLabel(self, text="Cargando...", justify="left")
        self.stats_label.grid(row=14, column=0, padx=20, pady=10, sticky="w")
        
        # Load saved configuration on startup
        self._load_configuration()
    
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
        
        # Baseline indicator (will be updated with arrow and percentage)
        self.baseline_indicator = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11))
        self.baseline_indicator.grid(row=5, column=0, padx=(120, 20), pady=(10, 0), sticky="w")
        
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
                    rejected: int, rejected_ap: int, total_peaks: int, baseline_mv: float = None):
        """Update statistics display."""
        text = f"Total Archivos: {total_files}\n"
        text += f"Aceptados (1): {accepted}\n"
        text += f"Afterpulses (>1): {afterpulse}\n"
        text += f"Rechazados (0): {rejected}\n"
        text += f"Rech. c/ AP (>1 raw): {rejected_ap}\n"
        text += f"Total Picos: {total_peaks}"
        self.stats_label.configure(text=text)
        
        # Update baseline indicator if provided
        if baseline_mv is not None and hasattr(self, 'baseline_indicator'):
            self._update_baseline_indicator(baseline_mv)
    
    
    def _update_baseline_indicator(self, baseline_mv: float):
        """Update baseline indicator with current value and comparison."""
        from utils.baseline_tracker import BaselineTracker
        
        tracker = BaselineTracker()
        comparison = tracker.get_comparison()
        
        if comparison is None:
            # No history yet, just show nothing or first measurement
            self.baseline_indicator.configure(text="", text_color="white")
        else:
            # Show arrow and percentage
            arrow = comparison['arrow']
            percentage = comparison['percentage']
            color_name = comparison['color']
            
            # Map color name to hex
            color_hex = "#2ecc71" if color_name == "green" else "#e74c3c"
            
            indicator_text = f"{arrow} {percentage:.1f}%"
            
            self.baseline_indicator.configure(
                text=indicator_text,
                text_color=color_hex
            )
    
    def _save_configuration(self):
        """Save current parameter values to configuration."""
        params = self.get_parameters()
        self.config.save_analysis_params(params)
        print("✓ Configuration saved!")
        
        # Visual feedback
        original_text = self.btn_save_config.cget("text")
        self.btn_save_config.configure(text="✓ Guardado!")
        self.after(2000, lambda: self.btn_save_config.configure(text=original_text))
    
    def _load_configuration(self):
        """Load saved parameter values from configuration."""
        saved_params = self.config.get_analysis_params()
        
        # Load prominence
        self.slider_prom.set(saved_params['prominence_pct'])
        self._update_prom_label(saved_params['prominence_pct'])
        
        # Load width
        self.entry_width.delete(0, 'end')
        self.entry_width.insert(0, str(saved_params['width_time'] * 1e6))
        
        # Load baseline
        self.entry_baseline.delete(0, 'end')
        self.entry_baseline.insert(0, str(saved_params['baseline_pct']))
        
        # Load max dist
        self.entry_maxdist.delete(0, 'end')
        self.entry_maxdist.insert(0, str(saved_params['max_dist_pct']))
        
        # Load afterpulse
        self.entry_afterpulse.delete(0, 'end')
        self.entry_afterpulse.insert(0, str(saved_params['afterpulse_pct']))
        
        # Load min distance
        self.entry_mindist.delete(0, 'end')
        self.entry_mindist.insert(0, str(saved_params['min_dist_time'] * 1e6))
