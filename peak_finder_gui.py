import customtkinter as ctk
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.signal import find_peaks
from pathlib import Path
import threading

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
DATA_DIR = Path(r"c:\Users\Ferna\Desktop\Laboratorio\analisis\SiPMG_LAr_DCR1_AMP")
WINDOW_TIME = 5e-6  # 5 microsegundos
NUM_POINTS = 4081
SAMPLE_TIME = WINDOW_TIME / NUM_POINTS

# Default Parameters
DEFAULT_PROMINENCE_PCT = 2.0  # Now in range 0.1-5%
DEFAULT_WIDTH_TIME = 0.2e-6
DEFAULT_MIN_DIST_TIME = 0.05e-6
DEFAULT_BASELINE_PCT = 85.0
DEFAULT_MAX_DIST_PCT = 99.0
DEFAULT_AFTERPULSE_PCT = 80.0

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PeakFinderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Peak Finder")
        self.geometry("1600x900")
        
        # Estado de la aplicación
        self.waveform_files = []
        self.accepted_results = []
        self.rejected_results = []
        self.afterpulse_results = []
        self.rejected_afterpulse_results = []
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_rejected_afterpulse_idx = 0
        self.global_max_amp = 0.01 # Default fallback
        self.global_min_amp = 0
        self.all_amplitudes_flat = np.array([])
        self.all_max_times = []
        self.baseline_low = 0
        self.baseline_high = 0
        self.max_dist_low = 0
        self.max_dist_high = 0
        self.afterpulse_low = 0
        self.afterpulse_high = 0
        
        # Configuración del grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Sidebar (Controles) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(20, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Peak Finder", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Parámetros
        self.create_parameter_controls()

        # Botón Actualizar
        self.btn_update = ctk.CTkButton(self.sidebar_frame, text="Actualizar Búsqueda", command=self.run_analysis)
        self.btn_update.grid(row=13, column=0, padx=20, pady=(20, 10))

        # Botón Distribución Temporal
        self.btn_timedist = ctk.CTkButton(self.sidebar_frame, text="Ver Dist. Temporal", command=self.show_time_distribution, fg_color="gray")
        self.btn_timedist.grid(row=14, column=0, padx=20, pady=(0, 10))
        
        # Botón Ver Todas las Waveforms
        self.btn_allwaveforms = ctk.CTkButton(self.sidebar_frame, text="Ver Todas Waveforms", command=self.show_all_waveforms, fg_color="gray")
        self.btn_allwaveforms.grid(row=15, column=0, padx=20, pady=(0, 20))

        # Stats Label
        self.stats_label = ctk.CTkLabel(self.sidebar_frame, text="Cargando...", justify="left")
        self.stats_label.grid(row=16, column=0, padx=20, pady=10, sticky="w")

        # --- Panel Superior Izquierdo (Aceptados - 1 Pico) ---
        self.tl_frame = ctk.CTkFrame(self)
        self.tl_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.tl_frame.grid_rowconfigure(0, weight=1)
        self.tl_frame.grid_columnconfigure(0, weight=1)
        
        self.tl_title = ctk.CTkLabel(self.tl_frame, text="Aceptados (1 Pico)", font=ctk.CTkFont(size=14, weight="bold"))
        self.tl_title.grid(row=1, column=0, pady=2)

        self.create_plot_area(self.tl_frame, "accepted")
        self.create_nav_controls(self.tl_frame, "accepted")

        # --- Panel Superior Derecho (Rechazados - 0 Picos) ---
        self.tr_frame = ctk.CTkFrame(self)
        self.tr_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.tr_frame.grid_rowconfigure(0, weight=1)
        self.tr_frame.grid_columnconfigure(0, weight=1)

        self.tr_title = ctk.CTkLabel(self.tr_frame, text="Rechazados (0 Picos)", font=ctk.CTkFont(size=14, weight="bold"))
        self.tr_title.grid(row=1, column=0, pady=2)

        self.create_plot_area(self.tr_frame, "rejected")
        self.create_nav_controls(self.tr_frame, "rejected")

        # --- Panel Inferior Izquierdo (Afterpulse - >1 Picos) ---
        self.bl_frame = ctk.CTkFrame(self)
        self.bl_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.bl_frame.grid_rowconfigure(0, weight=1)
        self.bl_frame.grid_columnconfigure(0, weight=1)

        self.bl_title = ctk.CTkLabel(self.bl_frame, text="Afterpulse (>1 Picos)", font=ctk.CTkFont(size=14, weight="bold"))
        self.bl_title.grid(row=1, column=0, pady=2)

        self.create_plot_area(self.bl_frame, "afterpulse")
        self.create_nav_controls(self.bl_frame, "afterpulse")

        # --- Panel Inferior Derecho (Rechazados con Afterpulses) ---
        self.br_frame = ctk.CTkFrame(self)
        self.br_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        self.br_frame.grid_rowconfigure(0, weight=1)
        self.br_frame.grid_columnconfigure(0, weight=1)
        
        self.br_title = ctk.CTkLabel(self.br_frame, text="Rechazados con Afterpulses", font=ctk.CTkFont(size=14, weight="bold"))
        self.br_title.grid(row=1, column=0, pady=2)

        self.create_plot_area(self.br_frame, "rejected_afterpulse")
        self.create_nav_controls(self.br_frame, "rejected_afterpulse")

        # Cargar datos e iniciar
        self.load_files()
        self.run_analysis()

    def create_parameter_controls(self):
        # Prominence
        self.lbl_prom = ctk.CTkLabel(self.sidebar_frame, text=f"Prominencia: {DEFAULT_PROMINENCE_PCT:.1f}%")
        self.lbl_prom.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.slider_prom = ctk.CTkSlider(self.sidebar_frame, from_=0.1, to=5.0, number_of_steps=49, command=self.update_prom_label)
        self.slider_prom.set(DEFAULT_PROMINENCE_PCT)
        self.slider_prom.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Width
        self.lbl_width = ctk.CTkLabel(self.sidebar_frame, text="Anchura Mínima (µs):")
        self.lbl_width.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_width = ctk.CTkEntry(self.sidebar_frame)
        self.entry_width.insert(0, str(DEFAULT_WIDTH_TIME * 1e6))
        self.entry_width.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Baseline %
        self.lbl_baseline = ctk.CTkLabel(self.sidebar_frame, text="Baseline (%):")
        self.lbl_baseline.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_baseline = ctk.CTkEntry(self.sidebar_frame)
        self.entry_baseline.insert(0, str(DEFAULT_BASELINE_PCT))
        self.entry_baseline.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Max Dist %
        self.lbl_maxdist = ctk.CTkLabel(self.sidebar_frame, text="Zona de Maximos (%):")
        self.lbl_maxdist.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_maxdist = ctk.CTkEntry(self.sidebar_frame)
        self.entry_maxdist.insert(0, str(DEFAULT_MAX_DIST_PCT))
        self.entry_maxdist.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Afterpulse %
        self.lbl_afterpulse = ctk.CTkLabel(self.sidebar_frame, text="Afterpulse (%):")
        self.lbl_afterpulse.grid(row=9, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_afterpulse = ctk.CTkEntry(self.sidebar_frame)
        self.entry_afterpulse.insert(0, str(DEFAULT_AFTERPULSE_PCT))
        self.entry_afterpulse.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Min Distance (µs)
        self.lbl_mindist = ctk.CTkLabel(self.sidebar_frame, text="Dist. Min. (µs):")
        self.lbl_mindist.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_mindist = ctk.CTkEntry(self.sidebar_frame)
        self.entry_mindist.insert(0, str(DEFAULT_MIN_DIST_TIME * 1e6))
        self.entry_mindist.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")

    def update_prom_label(self, value):
        self.lbl_prom.configure(text=f"Prominencia: {value:.1f}%")

    def create_plot_area(self, parent, side):
        # Matplotlib Figure
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        if side == "accepted":
            self.fig_acc = fig
            self.ax_acc = ax
            self.canvas_acc = canvas
        elif side == "rejected":
            self.fig_rej = fig
            self.ax_rej = ax
            self.canvas_rej = canvas
        elif side == "afterpulse":
            self.fig_ap = fig
            self.ax_ap = ax
            self.canvas_ap = canvas
        elif side == "rejected_afterpulse":
            self.fig_rap = fig
            self.ax_rap = ax
            self.canvas_rap = canvas

    def create_nav_controls(self, parent, side):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=2, column=0, pady=10)
        
        btn_prev = ctk.CTkButton(frame, text="← Anterior", width=100, 
                               command=lambda s=side: self.nav_prev(s))
        btn_prev.pack(side="left", padx=5)
        
        btn_next = ctk.CTkButton(frame, text="Siguiente →", width=100, 
                               command=lambda s=side: self.nav_next(s))
        btn_next.pack(side="left", padx=5)

    def load_files(self):
        self.waveform_files = sorted(DATA_DIR.glob("SiPMG_LAr_DCR1_*.txt"))
        print(f"Cargados {len(self.waveform_files)} archivos.")
        
        # Calculate global Y limits
        all_amps = []
        print("Calculando escala global, baseline y maximos...")
        min_vals = []
        max_vals = []
        all_data_list = []
        self.all_max_times = []
        
        for wf_file in self.waveform_files:
            try:
                with open(wf_file, 'r') as f:
                    lines = f.readlines()
                amps = np.array([float(line.strip()) for line in lines[2:] if line.strip()])
                min_vals.append(np.min(amps))
                max_vals.append(np.max(amps))
                all_data_list.append(amps)
                
                # Max time relative to trigger
                max_idx = np.argmax(amps)
                time_rel = (max_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                self.all_max_times.append(time_rel)
            except:
                pass
        
        if all_data_list:
            self.all_amplitudes_flat = np.concatenate(all_data_list)

        if min_vals and max_vals:
            self.global_min_amp = min(min_vals)
            real_max = max(max_vals)
            
            # Add some padding
            margin = (real_max - self.global_min_amp) * 0.1
            self.global_min_amp -= margin
            self.global_max_amp = real_max + margin
                
            print(f"Escala Global: {self.global_min_amp*1000:.2f}mV a {self.global_max_amp*1000:.2f}mV")

    def get_params(self):
        try:
            h = 0.0 # No explicit height threshold
            p_pct = self.slider_prom.get()
            # Convert % to absolute based on global range
            amp_range = self.global_max_amp - self.global_min_amp
            p = (p_pct / 100.0) * amp_range
            
            w = float(self.entry_width.get()) * 1e-6
            w_samples = int(w / SAMPLE_TIME)
            
            min_dist = float(self.entry_mindist.get()) * 1e-6
            min_dist_samples = int(min_dist / SAMPLE_TIME)
            if min_dist_samples < 1: min_dist_samples = 1

            b_pct = float(self.entry_baseline.get())
            m_pct = float(self.entry_maxdist.get())
            ap_pct = float(self.entry_afterpulse.get())
            return h, p, w_samples, min_dist_samples, b_pct, m_pct, ap_pct
        except ValueError:
            # Fallback calculation
            amp_range = self.global_max_amp - self.global_min_amp
            p = (DEFAULT_PROMINENCE_PCT / 100.0) * amp_range
            return 0.0, p, int(DEFAULT_WIDTH_TIME/SAMPLE_TIME), int(DEFAULT_MIN_DIST_TIME/SAMPLE_TIME), DEFAULT_BASELINE_PCT, DEFAULT_MAX_DIST_PCT, DEFAULT_AFTERPULSE_PCT

    def run_analysis(self):
        height, prominence, width, min_dist, baseline_pct, max_dist_pct, afterpulse_pct = self.get_params()
        
        # Calculate Baseline Range
        if len(self.all_amplitudes_flat) > 0:
            low_p = (100 - baseline_pct) / 2
            high_p = 100 - low_p
            self.baseline_low = np.percentile(self.all_amplitudes_flat, low_p)
            self.baseline_high = np.percentile(self.all_amplitudes_flat, high_p)
            print(f"Baseline ({baseline_pct}%): {self.baseline_low*1000:.2f}mV - {self.baseline_high*1000:.2f}mV")
            
        # Calculate Max Dist Range
        if len(self.all_max_times) > 0:
            low_p = (100 - max_dist_pct) / 2
            high_p = 100 - low_p
            self.max_dist_low = np.percentile(self.all_max_times, low_p)
            self.max_dist_high = np.percentile(self.all_max_times, high_p)
            print(f"Max Dist ({max_dist_pct}%): {self.max_dist_low*1e6:.2f}µs - {self.max_dist_high*1e6:.2f}µs")
        
        self.accepted_results = []
        self.rejected_results = []
        self.afterpulse_results = []
        self.rejected_afterpulse_results = []
        
        total_peaks = 0
        afterpulse_times = []
        
        for wf_file in self.waveform_files:
            try:
                with open(wf_file, 'r') as f:
                    lines = f.readlines()
                t_half = float(lines[0].strip())
                amplitudes = np.array([float(line.strip()) for line in lines[2:] if line.strip()])
                
                peaks, properties = find_peaks(
                    amplitudes,
                    height=height,
                    prominence=prominence,
                    width=0, # Capture all widths, filter later
                    distance=min_dist
                )
                
                # ===== SATURATION HANDLING =====
                # If multiple peaks are detected near saturation (close to global_max_amp),
                # merge them into a single peak (the one with max amplitude)
                if len(peaks) > 1:
                    saturation_threshold = self.global_max_amp * 0.95  # 95% of max
                    peak_amps = amplitudes[peaks]
                    
                    # Find peaks near saturation
                    saturated_mask = peak_amps >= saturation_threshold
                    
                    if np.sum(saturated_mask) > 1:
                        # Multiple saturated peaks detected - keep only the highest one
                        saturated_indices = np.where(saturated_mask)[0]  # Indices in peaks array
                        
                        # Find which saturated peak has max amplitude
                        max_sat_peak_idx = saturated_indices[np.argmax(peak_amps[saturated_indices])]
                        
                        # Create mask for peaks to keep: non-saturated + the max saturated one
                        keep_mask = ~saturated_mask  # Keep all non-saturated
                        keep_mask[max_sat_peak_idx] = True  # Keep the max saturated one
                        
                        # Filter peaks and properties
                        peaks = peaks[keep_mask]
                        for key in properties:
                            if isinstance(properties[key], np.ndarray) and len(properties[key]) == len(keep_mask):
                                properties[key] = properties[key][keep_mask]
                
                # Filter by Width manually
                # properties['widths'] contains the widths in samples
                peaks_passing_width = []
                if 'widths' in properties:
                    widths = properties['widths']
                    for i, p_idx in enumerate(peaks):
                        if widths[i] >= width:
                            peaks_passing_width.append(p_idx)
                else:
                    peaks_passing_width = peaks # Should not happen if width=0 is passed
                
                peaks_passing_width = np.array(peaks_passing_width)

                # Filter peaks based on Baseline
                # "Good" peaks are those above the baseline AND passing width.
                good_peaks = []
                if len(peaks_passing_width) > 0:
                    peak_times = (peaks_passing_width * SAMPLE_TIME) - (WINDOW_TIME / 2)
                    peak_amps = amplitudes[peaks_passing_width]
                    
                    for i, p_idx in enumerate(peaks_passing_width):
                        if peak_amps[i] > self.baseline_high:
                            good_peaks.append(p_idx)
                
                good_peaks = np.array(good_peaks)
                
                # Identify Main Peak Candidates (Good peaks inside Max Dist Zone)
                main_candidates = []
                for p_idx in good_peaks:
                    # Find index in original peaks array to get time/amp
                    # actually p_idx is the index in 'amplitudes'
                    # we need time.
                    # Let's just recalculate time for this p_idx
                    t = (p_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                    if self.max_dist_low <= t <= self.max_dist_high:
                        main_candidates.append(p_idx)
                
                result = {
                    'filename': wf_file.name,
                    't_half': t_half,
                    'amplitudes': amplitudes,
                    'peaks': np.array([]), # Placeholder
                    'all_peaks': peaks,
                    'properties': properties
                }

                # Classification
                if len(main_candidates) == 0:
                    # Rejected
                    if len(peaks) > 1:
                        self.rejected_afterpulse_results.append(result)
                    else:
                        self.rejected_results.append(result)
                else:
                    # Accepted or Afterpulse
                    # We have at least one valid main peak.
                    # If we have MORE than 1 "good" peak, it's an Afterpulse file.
                    if len(good_peaks) > 1:
                        # Afterpulse
                        result['peaks'] = good_peaks
                        self.afterpulse_results.append(result)
                        total_peaks += len(good_peaks)
                        
                        # Collect afterpulse times for statistics
                        # Identify the main peak (max amp among candidates? or max amp among all good peaks?)
                        # Usually main peak is the max amp one.
                        main_peak_idx = good_peaks[np.argmax(amplitudes[good_peaks])]
                        
                        for p_idx in good_peaks:
                            if p_idx != main_peak_idx:
                                t_ap = (p_idx * SAMPLE_TIME) - (WINDOW_TIME / 2)
                                afterpulse_times.append(t_ap)
                                
                    else:
                        # Accepted (Exactly 1 good peak, which is the main one)
                        result['peaks'] = good_peaks
                        self.accepted_results.append(result)
                        total_peaks += 1
                    
            except Exception as e:
                print(f"Error leyendo {wf_file}: {e}")

        # Calculate Afterpulse Range
        if len(afterpulse_times) > 0:
            low_p = (100 - afterpulse_pct) / 2
            high_p = 100 - low_p
            self.afterpulse_low = np.percentile(afterpulse_times, low_p)
            self.afterpulse_high = np.percentile(afterpulse_times, high_p)
            print(f"Afterpulse ({afterpulse_pct}%): {self.afterpulse_low*1e6:.2f}µs - {self.afterpulse_high*1e6:.2f}µs")
        else:
            self.afterpulse_low = 0
            self.afterpulse_high = 0

        # Reset indices
        self.current_accepted_idx = 0
        self.current_rejected_idx = 0
        self.current_afterpulse_idx = 0
        self.current_rejected_afterpulse_idx = 0
        
        # Update UI
        self.update_stats(total_peaks)
        self.update_plot("accepted")
        self.update_plot("rejected")
        self.update_plot("afterpulse")
        self.update_plot("rejected_afterpulse")

    def update_stats(self, total_peaks):
        text = f"Total Archivos: {len(self.waveform_files)}\n"
        text += f"Aceptados (1): {len(self.accepted_results)}\n"
        text += f"Afterpulses (>1): {len(self.afterpulse_results)}\n"
        text += f"Rechazados (0): {len(self.rejected_results)}\n"
        text += f"Rech. c/ AP (>1 raw): {len(self.rejected_afterpulse_results)}\n"
        text += f"Total Picos: {total_peaks}"
        self.stats_label.configure(text=text)
        
        self.tl_title.configure(text=f"Aceptados ({len(self.accepted_results)})")
        self.tr_title.configure(text=f"Rechazados ({len(self.rejected_results)})")
        self.bl_title.configure(text=f"Afterpulse ({len(self.afterpulse_results)})")
        self.br_title.configure(text=f"Rech. c/ AP ({len(self.rejected_afterpulse_results)})")

    def nav_next(self, side):
        if side == "accepted":
            if self.current_accepted_idx < len(self.accepted_results) - 1:
                self.current_accepted_idx += 1
                self.update_plot("accepted")
        elif side == "rejected":
            if self.current_rejected_idx < len(self.rejected_results) - 1:
                self.current_rejected_idx += 1
                self.update_plot("rejected")
        elif side == "afterpulse":
            if self.current_afterpulse_idx < len(self.afterpulse_results) - 1:
                self.current_afterpulse_idx += 1
                self.update_plot("afterpulse")
        elif side == "rejected_afterpulse":
            if self.current_rejected_afterpulse_idx < len(self.rejected_afterpulse_results) - 1:
                self.current_rejected_afterpulse_idx += 1
                self.update_plot("rejected_afterpulse")

    def nav_prev(self, side):
        if side == "accepted":
            if self.current_accepted_idx > 0:
                self.current_accepted_idx -= 1
                self.update_plot("accepted")
        elif side == "rejected":
            if self.current_rejected_idx > 0:
                self.current_rejected_idx -= 1
                self.update_plot("rejected")
        elif side == "afterpulse":
            if self.current_afterpulse_idx > 0:
                self.current_afterpulse_idx -= 1
                self.update_plot("afterpulse")
        elif side == "rejected_afterpulse":
            if self.current_rejected_afterpulse_idx > 0:
                self.current_rejected_afterpulse_idx -= 1
                self.update_plot("rejected_afterpulse")

    def update_plot(self, side):
        if side == "accepted":
            ax = self.ax_acc
            canvas = self.canvas_acc
            data_list = self.accepted_results
            idx = self.current_accepted_idx
            color_line = '#2ecc71' # Greenish
        elif side == "rejected":
            ax = self.ax_rej
            canvas = self.canvas_rej
            data_list = self.rejected_results
            idx = self.current_rejected_idx
            color_line = '#e74c3c' # Reddish
        elif side == "afterpulse":
            ax = self.ax_ap
            canvas = self.canvas_ap
            data_list = self.afterpulse_results
            idx = self.current_afterpulse_idx
            color_line = '#f1c40f' # Yellowish
        elif side == "rejected_afterpulse":
            ax = self.ax_rap
            canvas = self.canvas_rap
            data_list = self.rejected_afterpulse_results
            idx = self.current_rejected_afterpulse_idx
            color_line = '#9b59b6' # Purple

        ax.clear()
        
        if not data_list:
            ax.text(0.5, 0.5, "No hay datos", ha='center', va='center')
            canvas.draw()
            return

        data = data_list[idx]
        amplitudes = data['amplitudes']
        t_half = data['t_half']
        
        # Get valid peaks and all peaks
        valid_peaks = data['peaks']  # Good peaks that passed all filters
        all_peaks = data['all_peaks']  # All peaks initially detected
        
        # Time axis (Relative to center/trigger, 0 = center)
        t_axis = (np.arange(len(amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
        
        # Plot Waveform
        ax.plot(t_axis, amplitudes * 1000, color=color_line, linewidth=1, label='Signal')
        
        # Plot Baseline Area
        ax.axhspan(self.baseline_low * 1000, self.baseline_high * 1000, color='yellow', alpha=0.2, label='Baseline')
        
        # Plot Max Dist Area
        ax.axvspan(self.max_dist_low * 1e6, self.max_dist_high * 1e6, color='blue', alpha=0.15, label='Zona de Maximos')
        
        # Plot Afterpulse Area (Only in bottom plots)
        if side in ["afterpulse", "rejected_afterpulse"]:
            if self.afterpulse_low != 0 or self.afterpulse_high != 0:
                 ax.axvspan(self.afterpulse_low * 1e6, self.afterpulse_high * 1e6, color='green', alpha=0.15, label='Afterpulse')

        # Plot ALL detected peaks first (in red - rejected)
        if len(all_peaks) > 0:
            # Find rejected peaks (in all_peaks but not in valid_peaks)
            rejected_peaks = [p for p in all_peaks if p not in valid_peaks]
            if len(rejected_peaks) > 0:
                ax.plot(t_axis[rejected_peaks], amplitudes[rejected_peaks] * 1000, 'x', 
                       color='red', markeredgecolor='darkred', markersize=8, markeredgewidth=2, label='Rechazados')
        
        # Plot VALID peaks on top (in white - accepted)
        if len(valid_peaks) > 0:
            ax.plot(t_axis[valid_peaks], amplitudes[valid_peaks] * 1000, 'o', 
                   color='white', markeredgecolor='black', markersize=6, label='Válidos')

        ax.set_title(f"{data['filename']} - {len(valid_peaks)} Picos Válidos ({len(all_peaks)} Detectados)", fontsize=10)
        ax.set_xlabel("Tiempo (µs)", fontsize=8)
        ax.set_ylabel("Amplitud (mV)", fontsize=8)
        ax.set_ylim(self.global_min_amp * 1000, self.global_max_amp * 1000)
        ax.grid(True, alpha=0.3)
        
        canvas.draw()

    def show_time_distribution(self):
        if not self.accepted_results:
            return

        # 1. Collect all valid peaks with their GLOBAL times
        all_global_peaks = [] # List of (global_time, amplitude)
        
        # Combine accepted and afterpulse results for global analysis?
        # User said "una vez detectados todos los picos", likely implies all valid peaks found.
        all_results = self.accepted_results + self.afterpulse_results

        for res in all_results:
            t_half = res['t_half']
            peaks_indices = res['peaks'] # These are indices of VALID peaks
            amplitudes = res['amplitudes']
            
            # Calculate start time of this window
            t_start_window = t_half - (WINDOW_TIME / 2)
            
            for p_idx in peaks_indices:
                # Time relative to window start
                t_rel = p_idx * SAMPLE_TIME
                # Global time
                t_global = t_start_window + t_rel
                
                amp = amplitudes[p_idx]
                all_global_peaks.append((t_global, amp))

        if len(all_global_peaks) < 2:
            print("No hay suficientes picos para generar la distribución.")
            return

        # 2. Sort by global time
        all_global_peaks.sort(key=lambda x: x[0])
        
        # 3. Calculate differences
        times = np.array([p[0] for p in all_global_peaks])
        amps = np.array([p[1] for p in all_global_peaks])
        
        diffs = np.diff(times)
        # Amplitudes corresponding to the second peak in the pair
        amps_plot = amps[1:]
        
        # Create Floating Window
        top = ctk.CTkToplevel(self)
        top.title("Distribución Temporal Global")
        top.geometry("800x600")
        
        # Plot
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # X: Time diff (s)
        # User asked for "logaritmico" and "cuanto mas a la izquierda mas pequeño el periodo"
        # Log scale handles the "smaller is left" naturally.
        
        ax.scatter(diffs, amps_plot * 1000, alpha=0.6, s=15, c='#1f77b4', edgecolors='none')
        
        ax.set_xscale('log')
        ax.set_xlabel("Diferencia Temporal entre Picos Consecutivos (s) [Log]", fontsize=10)
        ax.set_ylabel("Amplitud del pico (mV)", fontsize=10)
        ax.set_title("Amplitud vs Delta T (Global)", fontsize=12)
        ax.grid(True, which="both", ls="-", alpha=0.2)
        
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ensure window stays on top after everything is drawn
        top.after(100, lambda: top.lift())
        top.after(100, lambda: top.focus_force())

    def show_all_waveforms(self):
        """Display all waveforms overlaid with improved visibility and proper zoom support."""
        if not self.waveform_files:
            print("No hay archivos cargados.")
            return
        
        # Create Floating Window
        top = ctk.CTkToplevel(self)
        top.title("Todas las Waveforms")
        top.geometry("1200x800")
        
        # Create frame for plot and toolbar
        plot_frame = ctk.CTkFrame(top)
        plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Plot
        fig = plt.Figure(figsize=(12, 8), dpi=100)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.08)
        
        num_files = len(self.waveform_files)
        print(f"Procesando {num_files} archivos...")
        
        # Better visibility settings - increased significantly for better visibility
        if num_files < 50:
            alpha_value = 0.7
            linewidth = 1.5
        elif num_files < 200:
            alpha_value = 0.45
            linewidth = 1.3
        elif num_files < 500:
            alpha_value = 0.3
            linewidth = 1.1
        else:
            # Even with 1000+ files, make them clearly visible
            alpha_value = 0.2
            linewidth = 1.0
        
        # Use a vibrant blue that looks great when overlaid
        waveform_color = '#1E90FF'  # DodgerBlue - vibrant and saturated
        
        for wf_file in self.waveform_files:
            try:
                with open(wf_file, 'r') as f:
                    lines = f.readlines()
                
                # First line contains t_half (time of the middle of the file)
                t_half = float(lines[0].strip())
                
                # Read amplitudes (skip first 2 lines: t_half and header/blank)
                amplitudes = np.array([float(line.strip()) for line in lines[2:] if line.strip()])
                
                # Calculate global time axis
                t_start = t_half - (WINDOW_TIME / 2)
                t_global = t_start + (np.arange(len(amplitudes)) * SAMPLE_TIME)
                
                # Plot this waveform with antialiasing for smoother appearance
                ax.plot(t_global * 1e6, amplitudes * 1000, 
                       color=waveform_color, 
                       alpha=alpha_value, 
                       linewidth=linewidth,
                       antialiased=True,
                       rasterized=False)  # Keep as vector for perfect zoom
                
            except Exception as e:
                print(f"Error procesando {wf_file}: {e}")
        
        ax.set_xlabel("Tiempo Global (µs)", fontsize=12, weight='bold')
        ax.set_ylabel("Amplitud (mV)", fontsize=12, weight='bold')
        ax.set_title(f"Todas las Waveforms Superpuestas ({num_files} archivos)", 
                    fontsize=14, weight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#cccccc')
        ax.set_ylim(self.global_min_amp * 1000, self.global_max_amp * 1000)
        
        # White background - much better for overlaid colored lines
        ax.set_facecolor('white')
        fig.patch.set_facecolor('#f0f0f0')
        ax.tick_params(colors='black', labelsize=10)
        ax.xaxis.label.set_color('black')
        ax.yaxis.label.set_color('black')
        ax.title.set_color('black')
        ax.spines['bottom'].set_color('black')
        ax.spines['top'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['right'].set_color('black')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        
        # Add navigation toolbar for zoom/pan functionality
        toolbar_frame = tk.Frame(plot_frame, bg='#f0f0f0')
        toolbar_frame.pack(side="top", fill="x")
        
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        toolbar.config(background='#f0f0f0')
        toolbar._message_label.config(background='#f0f0f0', foreground='black')
        
        # Pack canvas below toolbar
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        # Add instructions label
        info_label = ctk.CTkLabel(top, 
                                  text="💡 Usa la barra de herramientas: 🏠 Reset | ← → Navegar | 🔍 Zoom (selecciona área) | ✋ Pan (arrastra) | 🖱️ Click derecho para alejar",
                                  font=ctk.CTkFont(size=10))
        info_label.pack(side="bottom", pady=(0, 5))
        
        # Ensure window stays on top after everything is drawn
        top.after(100, lambda: top.lift())
        top.after(100, lambda: top.focus_force())

if __name__ == "__main__":
    app = PeakFinderApp()
    app.mainloop()

