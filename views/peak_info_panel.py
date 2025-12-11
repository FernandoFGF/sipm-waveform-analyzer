"""
Peak information panel widget for displaying detailed peak analysis.
"""
import customtkinter as ctk
import numpy as np
from config import WINDOW_TIME, SAMPLE_TIME
from models.analysis_results import WaveformResult


class PeakInfoPanel(ctk.CTkFrame):
    """Panel for displaying detailed peak information."""
    
    def __init__(self, parent):
        """
        Initialize peak information panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header with title and close button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Información de Picos",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.close_button = ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=30,
            command=self.hide_panel,
            fg_color="transparent",
            hover_color="#e74c3c",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.close_button.grid(row=0, column=1, sticky="e")
        
        # Scrollable text area for peak information
        self.text_area = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(size=12, family="Consolas")
        )
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Store callback for hiding
        self.on_hide = None
        
    def set_hide_callback(self, callback):
        """Set callback to be called when panel is hidden."""
        self.on_hide = callback
    
    def hide_panel(self):
        """Hide the panel."""
        if self.on_hide:
            self.on_hide()
    
    def show_peak_info(self, result: WaveformResult, baseline_high: float, 
                       max_dist_low: float, max_dist_high: float):
        """
        Display peak information for a waveform result.
        
        Args:
            result: WaveformResult to display
            baseline_high: Baseline threshold
            max_dist_low: Max distance zone lower bound
            max_dist_high: Max distance zone upper bound
        """
        # Enable editing to update content
        self.text_area.configure(state="normal")
        
        # Clear existing content
        self.text_area.delete("1.0", "end")
        
        # Header
        self.text_area.insert("end", f"═══════════════════════════════════════\n", "header")
        self.text_area.insert("end", f"Archivo: {result.filename}\n", "header")
        self.text_area.insert("end", f"═══════════════════════════════════════\n\n", "header")
        
        # Summary
        total_detected = len(result.all_peaks)
        total_accepted = len(result.peaks)
        total_rejected = total_detected - total_accepted
        
        self.text_area.insert("end", f"📈 Resumen:\n", "section")
        self.text_area.insert("end", f"  • Picos detectados: {total_detected}\n")
        self.text_area.insert("end", f"  • Picos aceptados: {total_accepted}\n", "accepted")
        self.text_area.insert("end", f"  • Picos rechazados: {total_rejected}\n\n", "rejected")
        
        # Detailed peak list
        self.text_area.insert("end", f"📋 Detalles de Picos:\n", "section")
        self.text_area.insert("end", f"{'─' * 50}\n\n")
        
        if total_detected == 0:
            self.text_area.insert("end", "  No se detectaron picos.\n\n")
        else:
            # Process all peaks
            for i, peak_idx in enumerate(result.all_peaks):
                # Calculate time and amplitude
                time_us = (peak_idx * SAMPLE_TIME - WINDOW_TIME / 2) * 1e6
                amplitude_mv = result.amplitudes[peak_idx] * 1000
                
                # Check if peak is accepted
                is_accepted = peak_idx in result.peaks
                
                # Peak header
                peak_num = i + 1
                status = "✓ ACEPTADO" if is_accepted else "✗ RECHAZADO"
                status_tag = "accepted" if is_accepted else "rejected"
                
                self.text_area.insert("end", f"Pico #{peak_num}: ", "bold")
                self.text_area.insert("end", f"{status}\n", status_tag)
                
                # Peak details
                self.text_area.insert("end", f"  ├─ Tiempo: {time_us:+.3f} µs\n")
                self.text_area.insert("end", f"  ├─ Amplitud: {amplitude_mv:.3f} mV\n")
                
                # Rejection reason if applicable
                if not is_accepted:
                    reason = result.peak_rejection_reasons.get(peak_idx, "Razón desconocida")
                    self.text_area.insert("end", f"  └─ Razón: {reason}\n", "reason")
                else:
                    # Check if in max dist zone
                    in_max_zone = max_dist_low <= (peak_idx * SAMPLE_TIME - WINDOW_TIME / 2) <= max_dist_high
                    zone_info = "Zona de máximos" if in_max_zone else "Fuera de zona de máximos"
                    self.text_area.insert("end", f"  └─ {zone_info}\n", "info")
                
                self.text_area.insert("end", "\n")
        
        # Configure tags for colored text (no font config - not supported by CTkTextbox)
        self.text_area.tag_config("header", foreground="#3498db")
        self.text_area.tag_config("section", foreground="#f39c12")
        self.text_area.tag_config("accepted", foreground="#2ecc71")
        self.text_area.tag_config("rejected", foreground="#e74c3c")
        self.text_area.tag_config("bold", foreground="#ffffff")
        self.text_area.tag_config("reason", foreground="#e67e22")
        self.text_area.tag_config("info", foreground="#95a5a6")
        
        # Disable editing
        self.text_area.configure(state="disabled")
