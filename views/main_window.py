"""
Main application window.
"""
import customtkinter as ctk

from config import (
    UI_THEME, UI_COLOR_THEME, MAIN_WINDOW_SIZE,
    COLOR_ACCEPTED, COLOR_REJECTED, COLOR_AFTERPULSE, COLOR_REJECTED_AFTERPULSE
)
from controllers.analysis_controller import AnalysisController
from views.control_sidebar import ControlSidebar
from views.plot_panel import PlotPanel
from views.popup_windows import show_temporal_distribution, show_all_waveforms


class MainWindow(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.title("Peak Finder")
        self.geometry(MAIN_WINDOW_SIZE)
        
        # Initialize controller
        self.controller = AnalysisController()
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create sidebar
        self.sidebar = ControlSidebar(
            self,
            on_update_analysis=self.run_analysis,
            on_show_temporal_dist=self.show_temporal_distribution,
            on_show_all_waveforms=self.show_all_waveforms
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Create plot panels
        self.panel_accepted = PlotPanel(
            self,
            "Aceptados (1 Pico)",
            COLOR_ACCEPTED,
            on_next=lambda: self.navigate_next("accepted"),
            on_prev=lambda: self.navigate_prev("accepted")
        )
        self.panel_accepted.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.panel_rejected = PlotPanel(
            self,
            "Rechazados (0 Picos)",
            COLOR_REJECTED,
            on_next=lambda: self.navigate_next("rejected"),
            on_prev=lambda: self.navigate_prev("rejected")
        )
        self.panel_rejected.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.panel_afterpulse = PlotPanel(
            self,
            "Afterpulse (>1 Picos)",
            COLOR_AFTERPULSE,
            on_next=lambda: self.navigate_next("afterpulse"),
            on_prev=lambda: self.navigate_prev("afterpulse")
        )
        self.panel_afterpulse.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.panel_rejected_afterpulse = PlotPanel(
            self,
            "Rechazados con Afterpulses",
            COLOR_REJECTED_AFTERPULSE,
            on_next=lambda: self.navigate_next("rejected_afterpulse"),
            on_prev=lambda: self.navigate_prev("rejected_afterpulse")
        )
        self.panel_rejected_afterpulse.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        
        # Load data and run initial analysis
        self.controller.load_data()
        self.run_analysis()
    
    def run_analysis(self):
        """Run analysis with current parameters."""
        params = self.sidebar.get_parameters()
        
        results = self.controller.run_analysis(**params)
        
        # Update stats
        self.sidebar.update_stats(
            total_files=self.controller.waveform_data.get_file_count(),
            accepted=results.get_accepted_count(),
            afterpulse=results.get_afterpulse_count(),
            rejected=results.get_rejected_count(),
            rejected_ap=results.get_rejected_afterpulse_count(),
            total_peaks=results.total_peaks
        )
        
        # Update panel titles
        self.panel_accepted.update_title(f"Aceptados ({results.get_accepted_count()})")
        self.panel_rejected.update_title(f"Rechazados ({results.get_rejected_count()})")
        self.panel_afterpulse.update_title(f"Afterpulse ({results.get_afterpulse_count()})")
        self.panel_rejected_afterpulse.update_title(
            f"Rech. c/ AP ({results.get_rejected_afterpulse_count()})"
        )
        
        # Update plots
        self.update_plot("accepted")
        self.update_plot("rejected")
        self.update_plot("afterpulse")
        self.update_plot("rejected_afterpulse")
    
    def navigate_next(self, category: str):
        """Navigate to next item in category."""
        if self.controller.navigate_next(category):
            self.update_plot(category)
    
    def navigate_prev(self, category: str):
        """Navigate to previous item in category."""
        if self.controller.navigate_prev(category):
            self.update_plot(category)
    
    def update_plot(self, category: str):
        """Update plot for a specific category."""
        results_list = self.controller.get_results_for_category(category)
        
        if category == "accepted":
            panel = self.panel_accepted
        elif category == "rejected":
            panel = self.panel_rejected
        elif category == "afterpulse":
            panel = self.panel_afterpulse
        else:  # rejected_afterpulse
            panel = self.panel_rejected_afterpulse
        
        if not results_list:
            panel.show_no_data()
            return
        
        idx = self.controller.get_current_index(category)
        result = results_list[idx]
        
        # Determine if we should show afterpulse zone
        show_afterpulse = category in ["afterpulse", "rejected_afterpulse"]
        
        panel.update_plot(
            result=result,
            global_min_amp=self.controller.waveform_data.global_min_amp,
            global_max_amp=self.controller.waveform_data.global_max_amp,
            baseline_low=self.controller.results.baseline_low,
            baseline_high=self.controller.results.baseline_high,
            max_dist_low=self.controller.results.max_dist_low,
            max_dist_high=self.controller.results.max_dist_high,
            afterpulse_low=self.controller.results.afterpulse_low,
            afterpulse_high=self.controller.results.afterpulse_high,
            show_afterpulse_zone=show_afterpulse
        )
    
    def show_temporal_distribution(self):
        """Show temporal distribution popup."""
        show_temporal_distribution(
            self,
            self.controller.results.accepted_results,
            self.controller.results.afterpulse_results
        )
    
    def show_all_waveforms(self):
        """Show all waveforms popup."""
        show_all_waveforms(
            self,
            self.controller.waveform_data.waveform_files,
            self.controller.waveform_data.global_min_amp,
            self.controller.waveform_data.global_max_amp
        )
