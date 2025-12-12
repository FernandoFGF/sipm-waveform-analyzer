"""
Export Controller
Handles data export operations.
"""
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from pathlib import Path

from models.analysis_results import AnalysisResults
from utils.export_utils import ResultsExporter

class ExportController:
    """
    Controller for exporting analysis results.
    """
    
    def __init__(self, parent_window: ctk.CTk):
        """
        Initialize ExportController.
        
        Args:
            parent_window: Parent window for dialogs
        """
        self.parent_window = parent_window

    def show_export_dialog(self, results: AnalysisResults, current_params: dict):
        """
        Show dialog to select export format and perform export.
        
        Args:
            results: Analysis results to export
            current_params: Current analysis parameters (for JSON metadata)
        """
        # Create custom dialog for format selection
        format_dialog = ctk.CTkToplevel(self.parent_window)
        format_dialog.title("Exportar Resultados")
        format_dialog.geometry("300x150")
        format_dialog.transient(self.parent_window)
        format_dialog.grab_set()
        
        # Center the dialog
        format_dialog.update_idletasks()
        try:
            x = (format_dialog.winfo_screenwidth() // 2) - (300 // 2)
            y = (format_dialog.winfo_screenheight() // 2) - (150 // 2)
            format_dialog.geometry(f"300x150+{x}+{y}")
        except:
            pass
        
        selected_format = [None]
        
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
        self.parent_window.wait_window(format_dialog)
        
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
            title="Guardar Resultados",
            parent=self.parent_window
        )
        
        if not filepath:
            return
        
        # Export based on format
        try:
            if file_ext == "csv":
                ResultsExporter.export_analysis_to_csv(results, filepath)
            else:
                ResultsExporter.export_analysis_to_json(results, filepath, current_params)
            
            print(f"✓ Resultados exportados exitosamente a {filepath}")
        except Exception as e:
            print(f"Error exportando resultados: {e}")
