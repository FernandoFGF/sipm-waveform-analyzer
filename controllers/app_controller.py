"""
Application Controller
Handles top-level application logic, navigation, and dialog coordination.
"""
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import shutil
import customtkinter as ctk

import config
from controllers.analysis_controller import AnalysisController
# Import popups locally to avoid circular imports if necessary, or at top if safe
# from views.popups import ... (Doing lazily in methods is often safer for GUIs)

class AppController:
    """
    Main application controller.
    Coordinators interactions between the main window, other controllers, and popups.
    """
    
    def __init__(self, main_window: ctk.CTk, analysis_controller: AnalysisController):
        """
        Initialize the AppController.
        
        Args:
            main_window: Reference to the main window view
            analysis_controller: Reference to the analysis controller
        """
        self.main_window = main_window
        self.analysis_controller = analysis_controller
        self.comparison_cache: Dict[str, AnalysisController] = {}

    def change_directory(self) -> bool:
        """
        Handle directory change request.
        
        Returns:
            True if directory changed, False otherwise
        """
        # Logic to handle directory reload is currently in MainWindow.
        # Ideally, MainWindow asks this controller to do it.
        # But MainWindow owns the UI updates.
        # For now, we'll keep the UI update in MainWindow but move the logic here?
        # Actually, MainWindow.on_directory_changed does:
        # 1. Recreate AnalysisController
        # 2. Clear cache
        # 3. Load data
        # 4. Run analysis
        # This is tightly coupled to MainWindow's state.
        pass

    def open_comparison_window(self):
        """Open the comparison configuration and window."""
        from views.popups import show_comparison_config_dialog, show_tabbed_comparison_window
        from utils.data_config_reader import read_data_config # This is still in utils? Yes.
        
        # Show configuration dialog
        result = show_comparison_config_dialog(self.main_window, config.DATA_DIR)
        
        if not result:
            return  # User cancelled
        
        dataset2_path, selected_options = result
        
        # Check cache
        if dataset2_path in self.comparison_cache:
            print(f"Usando controlador en caché para: {dataset2_path}")
            controller2 = self.comparison_cache[dataset2_path]
        else:
            print(f"Cargando y analizando Dataset 2: {dataset2_path}")
            # Configure temp params
            data_config = read_data_config(dataset2_path)
            
            # Store current config
            old_window_time = config.WINDOW_TIME
            old_trigger = config.TRIGGER_VOLTAGE
            old_num_points = config.NUM_POINTS
            old_sample_time = config.SAMPLE_TIME
            
            # Update config using robust recalculation
            config.recalculate_config(dataset2_path)
            
            # Create controller for dataset 2
            controller2 = AnalysisController(data_dir=dataset2_path)
            controller2.load_data()
            
            # Run analysis with standard parameters (or could ask user)
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
            self.main_window, 
            self.analysis_controller, 
            config.DATA_DIR,
            controller2,
            dataset2_path,
            selected_options
        )
    
    def save_waveform_set(self, category: str):
        """
        Save complete set of waveforms for a category.
        """
        from tkinter import filedialog
        
        # Get the results for this category
        results_list = self.analysis_controller.get_results_for_category(category)
        
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
        dataset_name = config.DATA_DIR.name
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
