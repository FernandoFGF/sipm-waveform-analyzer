"""
Main application window.
"""
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime

from config import (
    UI_THEME, UI_COLOR_THEME, MAIN_WINDOW_SIZE,
    COLOR_ACCEPTED, COLOR_REJECTED, COLOR_AFTERPULSE, COLOR_REJECTED_AFTERPULSE
)
from controllers.analysis_controller import AnalysisController
from views.control_sidebar import ControlSidebar
from views.plot_panel import PlotPanel
from views.peak_info_panel import PeakInfoPanel
from views.popups import show_temporal_distribution, show_all_waveforms, show_charge_histogram
from utils import ResultsExporter


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
        
        # Create peak info panel (hidden by default)
        self.info_panel = PeakInfoPanel(self)
        self.info_panel.set_hide_callback(self.hide_peak_info)
        # Panel will be shown in column 3 when needed
        
        # Save initial DATA_DIR as last opened
        from utils import get_config
        import config
        config_manager = get_config()
        config_manager.save_last_data_dir(str(config.DATA_DIR))
        
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
            rejected_ap=0,  # No longer tracking rejected_afterpulse separately
            total_peaks=results.total_peaks,
            baseline_mv=(results.baseline_high - results.baseline_low) * 1000  # Baseline amplitude in mV
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
        """Save complete set of waveforms for a category.
        
        Args:
            category: Category name (accepted, rejected, afterpulse, favorites)
        """
        from tkinter import filedialog
        import shutil
        import config
        from pathlib import Path
        
        # Get the results for this category
        results_list = self.controller.get_results_for_category(category)
        
        if not results_list:
            print(f"No hay waveforms en la categoría {category}")
            return
        
        # Create category name mapping
        category_names = {
            "accepted": "ACEPTADOS",
            "rejected": "RECHAZADOS",
            "afterpulse": "AFTERPULSES",
            "favorites": "FAVORITOS"
        }
        
        category_name = category_names.get(category, category.upper())
        
        # Get the dataset name from current DATA_DIR
        dataset_name = config.DATA_DIR.name
        
        # Suggested directory name
        suggested_name = f"{category_name}_{dataset_name}"
        
        # Ask user where to save
        save_dir = filedialog.askdirectory(
            title=f"Seleccionar directorio para guardar {category_name}",
            initialdir=str(config.DATA_DIR.parent)
        )
        
        if not save_dir:
            return  # User cancelled
        
        # Create the target directory
        target_dir = Path(save_dir) / suggested_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy waveform files
        copied_count = 0
        for result in results_list:
            source_file = config.DATA_DIR / result.filename
            if source_file.exists():
                target_file = target_dir / result.filename
                shutil.copy2(source_file, target_file)
                copied_count += 1
        
        # Also copy DATA.txt if it exists
        data_txt = config.DATA_DIR / "DATA.txt"
        if data_txt.exists():
            shutil.copy2(data_txt, target_dir / "DATA.txt")
        
        print(f"✓ Guardados {copied_count} archivos en: {target_dir}")
        print(f"  Categoría: {category_name}")
        print(f"  Dataset: {dataset_name}")

    
    def export_results(self):
        """Export analysis results to file."""
        # Create custom dialog for format selection
        format_dialog = ctk.CTkToplevel(self)
        format_dialog.title("Exportar Resultados")
        format_dialog.geometry("300x150")
        format_dialog.transient(self)
        format_dialog.grab_set()
        
        # Center the dialog
        format_dialog.update_idletasks()
        x = (format_dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (format_dialog.winfo_screenheight() // 2) - (150 // 2)
        format_dialog.geometry(f"300x150+{x}+{y}")
        
        selected_format = [None]  # Use list to allow modification in nested function
        
        def select_format(fmt):
            selected_format[0] = fmt
            format_dialog.destroy()
        
        # Label
        label = ctk.CTkLabel(
            format_dialog,
            text="Selecciona el formato de exportación:",
            font=ctk.CTkFont(size=13)
        )
        label.pack(pady=(20, 15))
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(format_dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # CSV button
        csv_btn = ctk.CTkButton(
            btn_frame,
            text="📄 CSV",
            command=lambda: select_format("csv"),
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        )
        csv_btn.pack(side="left", padx=10)
        
        # JSON button
        json_btn = ctk.CTkButton(
            btn_frame,
            text="📊 JSON",
            command=lambda: select_format("json"),
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2980b9",
            hover_color="#21618c"
        )
        json_btn.pack(side="left", padx=10)
        
        # Wait for dialog to close
        self.settings_window = None
        self.comparison_cache = {}  # Cache for comparison controllers: {path: controller}
        self.wait_window(format_dialog)
        
        if not selected_format[0]:
            return
        
        file_ext = selected_format[0]
        
        # Determine file types
        if file_ext == "csv":
            file_types = [("CSV files", "*.csv"), ("All files", "*.*")]
        else:
            file_types = [("JSON files", "*.json"), ("All files", "*.*")]
        
        # Ask for save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"analysis_results_{timestamp}.{file_ext}"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{file_ext}",
            filetypes=file_types,
            initialfile=default_filename,
            title="Guardar Resultados"
        )
        
        if not filepath:
            return
        
        # Export based on format
        try:
            if file_ext == "csv":
                ResultsExporter.export_analysis_to_csv(self.controller.results, filepath)
            else:
                params = self.sidebar.get_parameters()
                ResultsExporter.export_analysis_to_json(self.controller.results, filepath, params)
            
            print(f"✓ Resultados exportados exitosamente a {filepath}")
        except Exception as e:
            print(f"Error exportando resultados: {e}")
    
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
        from views.popups import show_comparison_config_dialog, show_tabbed_comparison_window
        from controllers.analysis_controller import AnalysisController
        from utils import read_data_config
        import config
        
        # Show configuration dialog
        result = show_comparison_config_dialog(self, config.DATA_DIR)
        
        if not result:
            return  # User cancelled
        
        # Ensure cache exists (for hot-reloading stability)
        if not hasattr(self, 'comparison_cache'):
            self.comparison_cache = {}
            
        dataset2_path, selected_options = result
        
        # Check cache
        if dataset2_path in self.comparison_cache:
            print(f"Usando controlador en caché para: {dataset2_path}")
            controller2 = self.comparison_cache[dataset2_path]
        else:
            print(f"Cargando y analizando Dataset 2: {dataset2_path}")
            # Configure temp params
            data_config = read_data_config(dataset2_path)
            old_window_time = config.WINDOW_TIME
            old_trigger = config.TRIGGER_VOLTAGE
            old_num_points = config.NUM_POINTS
            old_sample_time = config.SAMPLE_TIME
            
            # Update config temporarily
            if data_config:
                if 'window_time' in data_config:
                    config.WINDOW_TIME = data_config['window_time']
                if 'trigger_voltage' in data_config:
                    config.TRIGGER_VOLTAGE = data_config['trigger_voltage']
                if 'num_points' in data_config:
                    config.NUM_POINTS = data_config['num_points']
                    config.SAMPLE_TIME = config.WINDOW_TIME / config.NUM_POINTS
            
            # Create controller for dataset 2
            controller2 = AnalysisController(data_dir=dataset2_path)
            controller2.load_data()
            
            # Run analysis with same parameters
            params = {
                'prominence_pct': 2.0,
                'width_time': 0.2e-6,
                'min_dist_time': 0.05e-6,
                'baseline_pct': 85.0,
                'max_dist_pct': 99.0,
                'afterpulse_pct': 80.0
            }
            controller2.run_analysis(**params)
            
            # Cache the controller
            self.comparison_cache[dataset2_path] = controller2
            
            # Restore original config
            config.WINDOW_TIME = old_window_time
            config.TRIGGER_VOLTAGE = old_trigger
            config.NUM_POINTS = old_num_points
            config.SAMPLE_TIME = old_sample_time
        
        # Show tabbed comparison window
        show_tabbed_comparison_window(
            self, 
            self.controller, 
            config.DATA_DIR,
            controller2,
            dataset2_path,
            selected_options
        )
