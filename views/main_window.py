"""
Main application window.
"""
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
import threading
import queue
import sys

from config import (
    UI_THEME, UI_COLOR_THEME, MAIN_WINDOW_SIZE,
    COLOR_ACCEPTED, COLOR_REJECTED, COLOR_AFTERPULSE, COLOR_REJECTED_AFTERPULSE
)
from controllers.analysis_controller import AnalysisController
from controllers.app_controller import AppController
from controllers.export_controller import ExportController
from views.control_sidebar import ControlSidebar
from views.plot_panel import PlotPanel
from views.peak_info_panel import PeakInfoPanel
from views.popups import show_temporal_distribution, show_all_waveforms, show_charge_histogram


class MainWindow(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.title("Peak Finder")
        self.geometry(MAIN_WINDOW_SIZE)
        
        # Initialize controllers
        self.controller = AnalysisController()
        self.app_controller = AppController(self, self.controller)
        self.export_controller = ExportController(self)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)  # Status bar row
        
        # Create sidebar
        self.sidebar = ControlSidebar(
            self,
            on_update_analysis=self.run_analysis,
            on_show_temporal_dist=self.show_temporal_distribution,
            on_show_all_waveforms=self.show_all_waveforms,
            on_show_charge_histogram=self.show_charge_histogram,
            on_export_results=self.export_results,
            on_show_advanced_analysis=self.show_advanced_analysis,
            on_show_signal_processing=self.show_signal_processing
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Set callback for directory changes
        self.sidebar.set_directory_changed_callback(self.on_directory_changed)
        
        # Set callback for comparison window
        self.sidebar.set_comparison_callback(self.open_comparison_window)
        
        # Create plot panels with new layout:
        # Top-left: Aceptados | Top-right: Afterpulse
        # Bottom-left: Rechazados | Bottom-right: Favoritos
        
        self.panel_accepted = PlotPanel(
            self,
            "Aceptados (1 Pico)",
            COLOR_ACCEPTED,
            on_next=lambda: self.navigate_next("accepted"),
            on_prev=lambda: self.navigate_prev("accepted"),
            on_show_info=self.show_peak_info,
            on_add_favorite=self.add_to_favorites,
            on_remove_favorite=self.remove_from_favorites,
            check_is_favorite=self.is_favorite,
            category="accepted",
            on_save_set=self.save_waveform_set
        )
        self.panel_accepted.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.panel_afterpulse = PlotPanel(
            self,
            "Afterpulse (>1 Picos)",
            COLOR_AFTERPULSE,
            on_next=lambda: self.navigate_next("afterpulse"),
            on_prev=lambda: self.navigate_prev("afterpulse"),
            on_show_info=self.show_peak_info,
            on_add_favorite=self.add_to_favorites,
            on_remove_favorite=self.remove_from_favorites,
            check_is_favorite=self.is_favorite,
            category="afterpulse",
            on_save_set=self.save_waveform_set
        )
        self.panel_afterpulse.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.panel_rejected = PlotPanel(
            self,
            "Rechazados",
            COLOR_REJECTED,
            on_next=lambda: self.navigate_next("rejected"),
            on_prev=lambda: self.navigate_prev("rejected"),
            on_show_info=self.show_peak_info,
            on_add_favorite=self.add_to_favorites,
            on_remove_favorite=self.remove_from_favorites,
            check_is_favorite=self.is_favorite,
            category="rejected",
            on_save_set=self.save_waveform_set
        )
        self.panel_rejected.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.panel_favorites = PlotPanel(
            self,
            "Favoritos",
            "#f39c12",  # Orange color for favorites
            on_next=lambda: self.navigate_next("favorites"),
            on_prev=lambda: self.navigate_prev("favorites"),
            on_show_info=self.show_peak_info,
            on_add_favorite=self.add_to_favorites,
            on_remove_favorite=self.remove_from_favorites,
            check_is_favorite=self.is_favorite,
            category="favorites",
            on_save_set=self.save_waveform_set
        )
        self.panel_favorites.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        
        # Create status bar
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(family="Consolas", size=10),
            anchor="w",
            fg_color=("gray90", "gray20")
        )
        self.status_label.grid(row=2, column=0, columnspan=3, sticky="ew", padx=2, pady=2)
        
        # Redirect print to status bar
        sys.stdout = PrintRedirector(self.update_status)
        
        # Create peak info panel (hidden by default)
        self.info_panel = PeakInfoPanel(self)
        self.info_panel.set_hide_callback(self.hide_peak_info)
        # Panel will be shown in column 3 when needed
        
        # Threading infrastructure for background analysis
        self.analysis_queue = queue.Queue()
        self.analysis_running = False
        self._start_queue_checker()
        
        # Save initial DATA_DIR as last opened
        from utils import get_config
        import config
        config_manager = get_config()
        config_manager.save_last_data_dir(str(config.DATA_DIR))
        
        # Load data and run initial analysis
        self.controller.load_data()
        self.run_analysis()
    
    def _start_queue_checker(self):
        """Start periodic queue checking for analysis results."""
        self._check_analysis_queue()
    
    def _check_analysis_queue(self):
        """Check queue for messages from analysis thread (runs every 100ms)."""
        try:
            while True:
                msg_type, data = self.analysis_queue.get_nowait()
                
                if msg_type == "progress":
                    # Update progress (currently just print, could add progress bar)
                    print(f"Progreso: {data}")
                
                elif msg_type == "complete":
                    # Analysis finished successfully
                    self._update_ui_with_results(data)
                
                elif msg_type == "error":
                    # Analysis failed
                    print(f"Error en análisis: {data}")
                    self.sidebar.btn_update.configure(state="normal", text="Actualizar")
                    self.analysis_running = False
        
        except queue.Empty:
            pass
        
        # Schedule next check in 100ms
        self.after(100, self._check_analysis_queue)
    
    def run_analysis(self):
        """Run analysis in background thread to keep UI responsive."""
        if self.analysis_running:
            print("Análisis ya en ejecución...")
            return
        
        params = self.sidebar.get_parameters()
        
        # Disable update button and show status
        self.sidebar.btn_update.configure(state="disabled", text="Analizando...")
        self.analysis_running = True
        
        # Run analysis in background thread
        thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(params,),
            daemon=True
        )
        thread.start()
    
    def _run_analysis_thread(self, params):
        """Background thread worker for analysis."""
        try:
            results = self.controller.run_analysis(**params)
            self.analysis_queue.put(("complete", results))
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.analysis_queue.put(("error", error_msg))
    
    def _update_ui_with_results(self, results):
        """Update UI with analysis results (called from main thread)."""
        # Re-enable update button
        self.sidebar.btn_update.configure(state="normal", text="Actualizar")
        self.analysis_running = False
        
        # Update stats
        self.sidebar.update_stats(
            total_files=self.controller.waveform_data.get_file_count(),
            accepted=results.get_accepted_count(),
            afterpulse=results.get_afterpulse_count(),
            rejected=results.get_rejected_count(),
            rejected_ap=0,
            total_peaks=results.total_peaks,
            baseline_mv=(results.baseline_high - results.baseline_low) * 1000
        )
        
        # Update panel titles
        self.panel_accepted.update_title(f"Aceptados ({results.get_accepted_count()})")
        self.panel_afterpulse.update_title(f"Afterpulse ({results.get_afterpulse_count()})")
        self.panel_rejected.update_title(f"Rechazados ({results.get_rejected_count()})")
        self.panel_favorites.update_title(f"Favoritos ({results.get_favorites_count()})")
        
        # Update plots
        self.update_plot("accepted")
        self.update_plot("rejected")
        self.update_plot("afterpulse")
        self.update_plot("favorites")
    
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
        elif category == "favorites":
            panel = self.panel_favorites
        else:
            return  # Unknown category
        
        if not results_list:
            panel.show_no_data()
            return
        
        idx = self.controller.get_current_index(category)
        result = results_list[idx]
        
        # Determine if we should show afterpulse zone
        show_afterpulse = category == "afterpulse"
        
        # For favorites, get the original category
        original_category = None
        if category == "favorites":
            original_category = self.controller.results.get_favorite_original_category(result.filename)
        
        # Get current negative trigger value from sidebar
        params = self.sidebar.get_parameters()
        negative_trigger_mv = params.get('negative_trigger_mv', -10.0)
        
        panel.update_plot(
            result=result,
            global_min_amp=self.controller.waveform_data.global_min_amp,
            global_max_amp=self.controller.waveform_data.global_max_amp,
            baseline_low=self.controller.results.baseline_low,
            baseline_high=self.controller.results.baseline_high,
            max_dist_low=self.controller.results.max_dist_low,
            max_dist_high=self.controller.results.max_dist_high,
            negative_trigger_mv=negative_trigger_mv,
            original_category=original_category
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
        show_all_waveforms(self, self.controller)
    
    def show_charge_histogram(self):
        """Show charge histogram popup."""
        show_charge_histogram(
            self,
            self.controller.results.accepted_results,
            self.controller.results.baseline_high
        )
    
    def show_advanced_analysis(self):
        """Show advanced SiPM analysis window."""
        from views.popups import show_advanced_sipm_analysis
        show_advanced_sipm_analysis(
            self,
            self.controller.results,
            self.controller.waveform_data
        )
    
    def show_signal_processing(self):
        """Show signal processing window."""
        from views.popups import show_signal_processing
        show_signal_processing(
            self,
            self.controller.waveform_data,
            self.controller.results
        )
    
    def show_peak_info(self, result):
        """Show peak information panel for a waveform result."""
        # Show the info panel in column 3
        self.info_panel.grid(row=0, column=3, rowspan=2, padx=5, pady=5, sticky="nsew")
        
        # Display peak information
        self.info_panel.show_peak_info(
            result,
            self.controller.results.baseline_high,
            self.controller.results.max_dist_low,
            self.controller.results.max_dist_high
        )
    
    def hide_peak_info(self):
        """Hide peak information panel."""
        self.info_panel.grid_forget()
    
    def add_to_favorites(self, result):
        """Add a waveform to favorites."""
        self.controller.add_to_favorites(result)
        # Update title with new count
        self.panel_favorites.update_title(f"Favoritos ({self.controller.results.get_favorites_count()})")
        self.update_plot("favorites")  # Refresh favorites panel
    
    def remove_from_favorites(self, result):
        """Remove a waveform from favorites."""
        self.controller.remove_from_favorites(result.filename)
        # Update title with new count
        self.panel_favorites.update_title(f"Favoritos ({self.controller.results.get_favorites_count()})")
        self.update_plot("favorites")  # Refresh favorites panel
    
    def is_favorite(self, filename: str) -> bool:
        """Check if a waveform is in favorites."""
        return self.controller.is_favorite(filename)
    
    def save_waveform_set(self, category: str):
        """Save complete set of waveforms for a category."""
        self.app_controller.save_waveform_set(category)

    
    def export_results(self):
        """Export analysis results to file."""
        params = self.sidebar.get_parameters()
        self.export_controller.show_export_dialog(self.controller.results, params)
    
    def on_directory_changed(self):
        """Handle directory change - reload data and rerun analysis."""
        print("Recargando datos del nuevo directorio...")
        
        # Reinitialize the controller to clear old data, passing the new DATA_DIR
        from controllers.analysis_controller import AnalysisController
        import config
        self.controller = AnalysisController(data_dir=config.DATA_DIR)
        
        # Clear cache when main directory changes to free memory or avoid conflicts
        self.comparison_cache = {}
        
        # Load data from new directory
        self.controller.load_data()
        
        # Run analysis
        self.run_analysis()
        
        print("✓ Datos recargados y análisis completado")
    
    def open_comparison_window(self):
        """Open comparison configuration and then tabbed comparison window."""
        self.app_controller.open_comparison_window()
    
    def update_status(self, message: str):
        """Update status bar with message (thread-safe)."""
        # Schedule update on main thread
        self.after(0, lambda: self.status_label.configure(text=message))


class PrintRedirector:
    """Redirects print statements to both console and UI status bar."""
    
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.terminal = sys.__stdout__
        
    def write(self, message):
        # Write to terminal
        self.terminal.write(message)
        
        # Update status bar (only non-empty lines)
        if message.strip():
            self.status_callback(message.strip())
    
    def flush(self):
        self.terminal.flush()
