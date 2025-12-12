"""
Comparison configuration dialog for selecting datasets and comparison options.
"""
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path


class ComparisonConfigDialog(ctk.CTkToplevel):
    """Dialog to configure dataset comparison options."""
    
    def __init__(self, parent, current_data_dir):
        """Initialize comparison configuration dialog."""
        super().__init__(parent)
        
        self.title("Configurar Comparación")
        self.geometry("500x700")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.current_data_dir = current_data_dir
        self.selected_dir = None
        self.selected_options = []
        self.result = None  # Will be (dataset_path, options_list) or None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create UI
        self._create_dataset_selector()
        self._create_options_checkboxes()
        self._create_buttons()
        
        self.focus()
    
    def _create_dataset_selector(self):
        """Create dataset selection section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            frame,
            text="Seleccionar Dataset para Comparar",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Current dataset
        ctk.CTkLabel(
            frame,
            text=f"Dataset Actual: {self.current_data_dir.name}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=5)
        
        # Dataset 2 selector
        self.dataset2_label = ctk.CTkLabel(
            frame,
            text="Dataset 2: No seleccionado",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.dataset2_label.pack(pady=5)
        
        ctk.CTkButton(
            frame,
            text="Seleccionar Dataset 2",
            command=self._select_dataset,
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(pady=10)
    
    def _create_options_checkboxes(self):
        """Create checkboxes for comparison options."""
        # Scrollable frame for options
        scroll_frame = ctk.CTkScrollableFrame(self, label_text="Opciones de Comparación")
        scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Store checkbox variables
        self.checkbox_vars = {}
        
        # Define all available comparison options
        options = [
            ("visualization", "Visualización de Waveforms"),
            ("amplitude_distribution", "Distribución de Amplitudes"),
            ("temporal_distribution", "Distribución Temporal + FFT"),
            ("charge_histogram", "Histograma de Carga"),
            ("all_waveforms", "Waveform Completa"),
        ]
        
        # Create checkboxes
        for option_id, option_label in options:
            var = ctk.BooleanVar(value=False)
            self.checkbox_vars[option_id] = var
            
            checkbox = ctk.CTkCheckBox(
                scroll_frame,
                text=option_label,
                variable=var,
                font=ctk.CTkFont(size=13)
            )
            checkbox.pack(anchor="w", pady=8, padx=20)
        
        # Select/Deselect all buttons
        btn_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="Seleccionar Todo",
            command=self._select_all,
            width=120,
            height=30
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Deseleccionar Todo",
            command=self._deselect_all,
            width=120,
            height=30
        ).pack(side="left", padx=5)
    
    def _create_buttons(self):
        """Create action buttons."""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._cancel,
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).grid(row=0, column=0, padx=10, sticky="ew")
        
        ctk.CTkButton(
            btn_frame,
            text="Comparar",
            command=self._confirm,
            fg_color="#27ae60",
            hover_color="#229954"
        ).grid(row=0, column=1, padx=10, sticky="ew")
    
    def _select_dataset(self):
        """Select second dataset."""
        selected_dir = filedialog.askdirectory(
            title="Seleccionar Dataset 2",
            initialdir=str(self.current_data_dir.parent)
        )
        
        if selected_dir:
            self.selected_dir = Path(selected_dir)
            self.dataset2_label.configure(
                text=f"Dataset 2: {self.selected_dir.name}",
                text_color="white"
            )
    
    def _select_all(self):
        """Select all checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(True)
    
    def _deselect_all(self):
        """Deselect all checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(False)
    
    def _confirm(self):
        """Confirm and close dialog."""
        if not self.selected_dir:
            # Show error - no dataset selected
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("300x150")
            error_dialog.transient(self)
            error_dialog.grab_set()
            
            ctk.CTkLabel(
                error_dialog,
                text="⚠️ Error",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)
            
            ctk.CTkLabel(
                error_dialog,
                text="Debes seleccionar un Dataset 2",
                font=ctk.CTkFont(size=12)
            ).pack(pady=10)
            
            ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy
            ).pack(pady=10)
            
            return
        
        # Get selected options
        self.selected_options = [
            option_id for option_id, var in self.checkbox_vars.items()
            if var.get()
        ]
        
        if not self.selected_options:
            # Show error - no options selected
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("350x150")
            error_dialog.transient(self)
            error_dialog.grab_set()
            
            ctk.CTkLabel(
                error_dialog,
                text="⚠️ Error",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)
            
            ctk.CTkLabel(
                error_dialog,
                text="Debes seleccionar al menos una opción",
                font=ctk.CTkFont(size=12)
            ).pack(pady=10)
            
            ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy
            ).pack(pady=10)
            
            return
        
        # Set result and close
        self.result = (self.selected_dir, self.selected_options)
        self.grab_release()
        self.destroy()
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def get_result(self):
        """Get the result after dialog closes."""
        self.wait_window()
        return self.result


def show_comparison_config_dialog(parent, current_data_dir):
    """
    Show comparison configuration dialog.
    
    Returns:
        tuple: (dataset_path, options_list) or None if cancelled
    """
    dialog = ComparisonConfigDialog(parent, current_data_dir)
    return dialog.get_result()
