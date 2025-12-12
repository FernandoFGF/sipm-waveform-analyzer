"""
Reusable plot panel component for displaying waveforms.
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import WINDOW_TIME, SAMPLE_TIME, COLOR_ACCEPTED, COLOR_REJECTED, COLOR_AFTERPULSE, COLOR_REJECTED_AFTERPULSE
from models.analysis_results import WaveformResult
from utils.plotting import save_figure


class PlotPanel(ctk.CTkFrame):
    """Reusable panel for displaying waveform plots."""
    
    def __init__(self, parent, title: str, color: str, on_next, on_prev, on_show_info=None, 
                 on_add_favorite=None, on_remove_favorite=None, check_is_favorite=None,
                 category: str = None, on_save_set=None):
        """
        Initialize plot panel.
        
        Args:
            parent: Parent widget
            title: Panel title
            color: Line color for waveforms
            on_next: Callback for next button
            on_prev: Callback for previous button
            on_show_info: Callback for showing peak information
            on_add_favorite: Callback for adding to favorites
            on_remove_favorite: Callback for removing from favorites
            check_is_favorite: Callback to check if current result is favorite
            category: Category name (accepted, rejected, afterpulse, favorites)
            on_save_set: Callback for saving complete set
        """
        super().__init__(parent)
        
        self.title_text = title
        self.color = color
        self.on_next = on_next
        self.on_prev = on_prev
        self.on_show_info = on_show_info
        self.on_add_favorite = on_add_favorite
        self.on_remove_favorite = on_remove_favorite
        self.check_is_favorite = check_is_favorite
        self.category = category
        self.on_save_set = on_save_set
        self.current_result = None  # Store current result for info display
        
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

        # Setup context menu
        self._setup_context_menu()

    def _setup_context_menu(self):
        """Setup right-click context menu for export."""
        import tkinter as tk
        
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📊 Mostrar Información", command=self._show_peak_info)
        self.context_menu.add_separator()
        
        # Favorites options (will be shown/hidden dynamically)
        self.add_favorite_index = self.context_menu.index("end") + 1
        self.context_menu.add_command(label="⭐ Añadir a Favoritos", command=self._add_to_favorites)
        
        self.remove_favorite_index = self.context_menu.index("end") + 1
        self.context_menu.add_command(label="❌ Quitar de Favoritos", command=self._remove_from_favorites)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💾 Guardar como PNG", command=lambda: self._save_plot("png"))
        self.context_menu.add_command(label="💾 Guardar como PDF", command=lambda: self._save_plot("pdf"))
        self.context_menu.add_command(label="💾 Guardar como SVG", command=lambda: self._save_plot("svg"))
        
        # Add save set option if callback is provided
        if self.on_save_set and self.category:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="📦 Guardar Set Completo", command=self._save_set)
        
        # Bind right click to canvas
        self.canvas.get_tk_widget().bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Show context menu and update favorites options visibility."""
        # Update favorites menu items based on current state
        if self.current_result and self.check_is_favorite:
            is_fav = self.check_is_favorite(self.current_result.filename)
            
            # Show/hide appropriate option
            if is_fav:
                self.context_menu.entryconfig(self.add_favorite_index, state="disabled")
                self.context_menu.entryconfig(self.remove_favorite_index, state="normal")
            else:
                self.context_menu.entryconfig(self.add_favorite_index, state="normal")
                self.context_menu.entryconfig(self.remove_favorite_index, state="disabled")
        else:
            # Disable both if no callbacks
            self.context_menu.entryconfig(self.add_favorite_index, state="disabled")
            self.context_menu.entryconfig(self.remove_favorite_index, state="disabled")
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _save_plot(self, fmt):
        """Save plot to file."""
        save_figure(self.fig, default_prefix="waveform")
    
    def _show_peak_info(self):
        """Show peak information panel."""
        if self.on_show_info and self.current_result:
            self.on_show_info(self.current_result)
    
    def _add_to_favorites(self):
        """Add current waveform to favorites."""
        if self.on_add_favorite and self.current_result:
            self.on_add_favorite(self.current_result)
    
    def _remove_from_favorites(self):
        """Remove current waveform from favorites."""
        if self.on_remove_favorite and self.current_result:
            self.on_remove_favorite(self.current_result)
    
    def _save_set(self):
        """Save complete set of waveforms for this category."""
        if self.on_save_set and self.category:
            self.on_save_set(self.category)
    
    
    def update_plot(
        self,
        result: WaveformResult,
        global_min_amp: float,
        global_max_amp: float,
        baseline_low: float,
        baseline_high: float,
        max_dist_low: float,
        max_dist_high: float,
        negative_trigger_mv: float = -10.0,
        original_category: str = None
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
            negative_trigger_mv: Negative trigger threshold in mV
            original_category: Original category for favorites (accepted/rejected/afterpulse)
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
        
        
        # Note: Afterpulse zone visualization removed (parameter no longer used)
        
        # Plot rejected peaks (in all_peaks but not in valid_peaks)
        # Convert to sets for proper comparison
        valid_peaks_set = set(valid_peaks.tolist() if hasattr(valid_peaks, 'tolist') else valid_peaks)
        all_peaks_set = set(all_peaks.tolist() if hasattr(all_peaks, 'tolist') else all_peaks)
        rejected_peaks_indices = list(all_peaks_set - valid_peaks_set)
        
        if len(rejected_peaks_indices) > 0:
            rejected_peaks_array = np.array(sorted(rejected_peaks_indices))
            self.ax.plot(t_axis[rejected_peaks_array], amplitudes[rejected_peaks_array] * 1000, 'x',
                        color='red', markeredgecolor='darkred', markersize=10, 
                        markeredgewidth=2.5, label='Rechazados', zorder=5)
        
        # Plot valid peaks
        if len(valid_peaks) > 0:
            self.ax.plot(t_axis[valid_peaks], amplitudes[valid_peaks] * 1000, 'o',
                        color='white', markeredgecolor='black', markersize=6, label='Válidos', zorder=4)
        
        # Plot trigger line (dotted line at trigger voltage)
        from config import TRIGGER_VOLTAGE
        self.ax.axhline(y=TRIGGER_VOLTAGE * 1000, color='purple', linestyle=':', 
                       linewidth=2, label=f'Trigger ({TRIGGER_VOLTAGE:.2f}V)', alpha=0.7)
        
        # Plot negative trigger line (dotted line at negative threshold)
        self.ax.axhline(y=negative_trigger_mv, color='red', linestyle=':', 
                       linewidth=2, label=f'Trigger Neg. ({negative_trigger_mv:.1f}mV)', alpha=0.7)
        
        # Set plot title with optional category badge
        title = result.filename
        if original_category:
            # Add category badge
            category_labels = {
                "accepted": "✓ Aceptado",
                "rejected": "✗ Rechazado",
                "afterpulse": "⚡ Afterpulse"
            }
            badge = category_labels.get(original_category, "")
            if badge:
                title = f"{result.filename}\n[{badge}]"
        
        self.ax.set_title(title, fontsize=10)
        self.ax.set_xlabel('Tiempo (µs)')
        self.ax.set_ylabel('Amplitud (mV)')
        self.ax.set_ylim(global_min_amp * 1000, global_max_amp * 1000)
        self.ax.grid(True, alpha=0.3)
        
        # Store current result for info display
        self.current_result = result
        
        self.canvas.draw()
    
    def show_no_data(self):
        """Display 'no data' message."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No hay datos", ha='center', va='center')
        self.canvas.draw()
    
    def update_title(self, title: str):
        """Update panel title."""
        self.title_label.configure(text=title)
