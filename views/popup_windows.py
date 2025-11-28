"""
Popup windows for temporal distribution and all waveforms visualization.
"""
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

from config import WINDOW_TIME, SAMPLE_TIME, COLOR_WAVEFORM_OVERLAY
from utils import get_config, ResultsExporter


def show_temporal_distribution(parent, accepted_results, afterpulse_results):
    """
    Show temporal distribution of all peaks with SiPM analysis.
    
    Args:
        parent: Parent window
        accepted_results: List of accepted results
        afterpulse_results: List of afterpulse results
    """
    if not accepted_results:
        return
    
    # Import SiPM analyzer
    from models.sipm_analyzer import SiPMAnalyzer
    
    # Create window
    top = ctk.CTkToplevel(parent)
    top.title("Distribución Temporal Global - Análisis SiPM")
    top.geometry("1200x700")
    
    # Create main frame with two columns
    main_frame = ctk.CTkFrame(top)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=3)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)
    
    # Left: Plot
    plot_frame = ctk.CTkFrame(main_frame)
    plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    
    # Right: Metrics panel
    metrics_frame = ctk.CTkFrame(main_frame)
    metrics_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    
    # Collect all valid peaks with global times
    all_global_peaks = []
    all_results = accepted_results + afterpulse_results
    
    for res in all_results:
        t_half = res.t_half
        peaks_indices = res.peaks
        amplitudes = res.amplitudes
        
        t_start_window = t_half - (WINDOW_TIME / 2)
        
        for p_idx in peaks_indices:
            t_rel = p_idx * SAMPLE_TIME
            t_global = t_start_window + t_rel
            amp = amplitudes[p_idx]
            all_global_peaks.append((t_global, amp))
    
    if len(all_global_peaks) < 2:
        print("No hay suficientes picos para generar la distribución.")
        top.destroy()
        return
    
    # Sort by global time
    all_global_peaks.sort(key=lambda x: x[0])
    
    # Calculate differences
    times = np.array([p[0] for p in all_global_peaks])
    amps = np.array([p[1] for p in all_global_peaks])
    
    diffs = np.diff(times)
    amps_plot = amps[1:] * 1000  # Convert to mV
    
    # Variables to store current canvas and metrics widgets
    canvas_ref = {'canvas': None, 'fig': None}
    metrics_widgets = {'widgets': [], 'metrics': None}  # Store metrics object
    
    def update_plot(amp_threshold, time_threshold):
        """Update plot and metrics with new thresholds."""
        # Perform SiPM analysis with new thresholds
        analyzer = SiPMAnalyzer(amplitude_threshold_mV=amp_threshold, 
                               time_threshold_s=time_threshold)
        metrics = analyzer.analyze(diffs, amps_plot)
        
        # Store metrics for export
        metrics_widgets['metrics'] = metrics
        
        # Clear previous plot if exists
        if canvas_ref['canvas'] is not None:
            canvas_ref['canvas'].get_tk_widget().destroy()
        
        # Create new plot
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot points colored by region
        # DCR (bottom-right) - blue
        if metrics.dcr_mask is not None and np.any(metrics.dcr_mask):
            ax.scatter(diffs[metrics.dcr_mask], amps_plot[metrics.dcr_mask], 
                      alpha=0.6, s=15, c='#1f77b4', label='DCR', edgecolors='none')
        
        # Afterpulses (bottom-left) - green
        if metrics.afterpulse_mask is not None and np.any(metrics.afterpulse_mask):
            ax.scatter(diffs[metrics.afterpulse_mask], amps_plot[metrics.afterpulse_mask],
                      alpha=0.6, s=15, c='#2ecc71', label='Afterpulses', edgecolors='none')
        
        # Crosstalk (top-right) - red
        if metrics.crosstalk_mask is not None and np.any(metrics.crosstalk_mask):
            ax.scatter(diffs[metrics.crosstalk_mask], amps_plot[metrics.crosstalk_mask],
                      alpha=0.6, s=15, c='#e74c3c', label='Crosstalk', edgecolors='none')
        
        # AP + XT (top-left) - orange
        if metrics.crosstalk_afterpulse_mask is not None and np.any(metrics.crosstalk_afterpulse_mask):
            ax.scatter(diffs[metrics.crosstalk_afterpulse_mask], amps_plot[metrics.crosstalk_afterpulse_mask],
                      alpha=0.6, s=15, c='#ff9500', label='AP + XT', edgecolors='none')
        
        # Draw threshold lines
        # Horizontal line (amplitude threshold)
        ax.axhline(y=metrics.amplitude_threshold, color='red', linestyle='--', 
                  linewidth=2, label=f'Threshold Amp: {metrics.amplitude_threshold:.1f} mV')
        
        # Vertical line (time threshold)
        ax.axvline(x=metrics.time_threshold, color='purple', linestyle='--',
                  linewidth=2, label=f'Threshold Time: {metrics.time_threshold*1e6:.1f} µs')
        
        ax.set_xscale('log')
        ax.set_xlabel("Diferencia Temporal entre Picos Consecutivos (s) [Log]", fontsize=10)
        ax.set_ylabel("Amplitud del pico (mV)", fontsize=10)
        ax.set_title("Amplitud vs Delta T (Global) - Análisis SiPM", fontsize=12, weight='bold')
        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.legend(loc='upper right', fontsize=8)
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Store references
        canvas_ref['canvas'] = canvas
        canvas_ref['fig'] = fig
        
        # Update metrics display
        update_metrics_display(metrics)
    
    def update_metrics_display(metrics):
        """Update the metrics panel with new values."""
        # Clear existing metrics widgets
        for widget in metrics_widgets['widgets']:
            widget.destroy()
        metrics_widgets['widgets'].clear()
        
        # Total events
        total_label = ctk.CTkLabel(
            metrics_frame,
            text=f"Total de Eventos: {metrics.total_events:,}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        total_label.pack(pady=(0, 15))
        metrics_widgets['widgets'].append(total_label)
        
        # Crosstalk section
        xt_frame = ctk.CTkFrame(metrics_frame, fg_color="#2b2b2b")
        xt_frame.pack(fill="x", padx=10, pady=5)
        metrics_widgets['widgets'].append(xt_frame)
        
        xt_title = ctk.CTkLabel(xt_frame, text="Crosstalk (XT)", 
                               font=ctk.CTkFont(size=13, weight="bold"))
        xt_title.pack(pady=(10, 5))
        
        xt_pct = ctk.CTkLabel(xt_frame, text=f"{metrics.crosstalk_pct:.2f}%",
                             font=ctk.CTkFont(size=20, weight="bold"),
                             text_color="#e74c3c")
        xt_pct.pack()
        
        xt_count = ctk.CTkLabel(xt_frame, text=f"Eventos: {metrics.crosstalk_count:,}",
                               font=ctk.CTkFont(size=10))
        xt_count.pack(pady=(0, 10))
        
        # Afterpulses section
        ap_frame = ctk.CTkFrame(metrics_frame, fg_color="#2b2b2b")
        ap_frame.pack(fill="x", padx=10, pady=5)
        metrics_widgets['widgets'].append(ap_frame)
        
        ap_title = ctk.CTkLabel(ap_frame, text="Afterpulses (AP)",
                               font=ctk.CTkFont(size=13, weight="bold"))
        ap_title.pack(pady=(10, 5))
        
        ap_pct = ctk.CTkLabel(ap_frame, text=f"{metrics.afterpulse_pct:.2f}%",
                             font=ctk.CTkFont(size=20, weight="bold"),
                             text_color="#2ecc71")
        ap_pct.pack()
        
        ap_count = ctk.CTkLabel(ap_frame, text=f"Eventos: {metrics.afterpulse_count:,}",
                               font=ctk.CTkFont(size=10))
        ap_count.pack(pady=(0, 10))
        
        # AP + XT section
        ap_xt_frame = ctk.CTkFrame(metrics_frame, fg_color="#2b2b2b")
        ap_xt_frame.pack(fill="x", padx=10, pady=5)
        metrics_widgets['widgets'].append(ap_xt_frame)
        
        ap_xt_title = ctk.CTkLabel(ap_xt_frame, text="AP + XT",
                                  font=ctk.CTkFont(size=13, weight="bold"))
        ap_xt_title.pack(pady=(10, 5))
        
        ap_xt_pct = ctk.CTkLabel(ap_xt_frame, text=f"{metrics.crosstalk_afterpulse_pct:.2f}%",
                                font=ctk.CTkFont(size=20, weight="bold"),
                                text_color="#ff9500")
        ap_xt_pct.pack()
        
        ap_xt_count = ctk.CTkLabel(ap_xt_frame, text=f"Eventos: {metrics.crosstalk_afterpulse_count:,}",
                                  font=ctk.CTkFont(size=10))
        ap_xt_count.pack(pady=(0, 10))
        
        # DCR section
        dcr_frame = ctk.CTkFrame(metrics_frame, fg_color="#2b2b2b")
        dcr_frame.pack(fill="x", padx=10, pady=5)
        metrics_widgets['widgets'].append(dcr_frame)
        
        dcr_title = ctk.CTkLabel(dcr_frame, text="DCR (Dark Count Rate)",
                                font=ctk.CTkFont(size=13, weight="bold"))
        dcr_title.pack(pady=(10, 5))
        
        # Display both DCR calculation methods
        if metrics.dcr_count > 0 and metrics.dcr_rate_total_hz > 0:
            # Method 1: Total rate
            dcr_total_display = f"{metrics.dcr_rate_total_hz:.1f} Hz" if metrics.dcr_rate_total_hz < 1000 else f"{metrics.dcr_rate_total_hz/1000:.2f} kHz"
            dcr_total_label = ctk.CTkLabel(
                dcr_frame, 
                text=f"Método 1: {dcr_total_display}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#3498db"
            )
            dcr_total_label.pack()
            
            dcr_total_desc = ctk.CTkLabel(
                dcr_frame,
                text="(eventos / tiempo total)",
                font=ctk.CTkFont(size=9),
                text_color="gray"
            )
            dcr_total_desc.pack()
            
            # Method 2: Average rate
            dcr_avg_display = f"{metrics.dcr_rate_avg_hz:.1f} Hz" if metrics.dcr_rate_avg_hz < 1000 else f"{metrics.dcr_rate_avg_hz/1000:.2f} kHz"
            dcr_avg_label = ctk.CTkLabel(
                dcr_frame,
                text=f"Método 2: {dcr_avg_display}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#9b59b6"
            )
            dcr_avg_label.pack(pady=(5, 0))
            
            dcr_avg_desc = ctk.CTkLabel(
                dcr_frame,
                text="(1 / intervalo promedio)",
                font=ctk.CTkFont(size=9),
                text_color="gray"
            )
            dcr_avg_desc.pack()
            
            # Explanation of difference
            diff_pct = abs(metrics.dcr_rate_total_hz - metrics.dcr_rate_avg_hz) / metrics.dcr_rate_total_hz * 100
            diff_label = ctk.CTkLabel(
                dcr_frame,
                text=f"Diferencia: {diff_pct:.1f}%",
                font=ctk.CTkFont(size=9),
                text_color="#e67e22"
            )
            diff_label.pack(pady=(5, 0))
        else:
            dcr_placeholder = ctk.CTkLabel(dcr_frame, text="Sin eventos DCR",
                                          font=ctk.CTkFont(size=12),
                                          text_color="gray")
            dcr_placeholder.pack()
        
        dcr_count_label = ctk.CTkLabel(dcr_frame, text=f"Eventos: {metrics.dcr_count:,}",
                                      font=ctk.CTkFont(size=10))
        dcr_count_label.pack(pady=(5, 10))

    
    def on_update_button():
        """Handle update button click."""
        try:
            amp_val = float(amp_entry.get())
            time_val = float(time_entry.get()) * 1e-6  # Convert from µs to s
            update_plot(amp_val, time_val)
        except ValueError:
            print("Error: Por favor ingresa valores numéricos válidos")
    
    def on_save_config():
        """Save current threshold values to configuration."""
        try:
            amp_val = float(amp_entry.get())
            time_val = float(time_entry.get())
            config = get_config()
            config.save_sipm_thresholds(amp_val, time_val)
            print("✓ SiPM thresholds saved!")
            
            # Visual feedback
            original_text = save_config_btn.cget("text")
            save_config_btn.configure(text="✓ Guardado!")
            top.after(2000, lambda: save_config_btn.configure(text=original_text))
        except ValueError:
            print("Error: Valores inválidos")
    
    # Create metrics title
    metrics_title = ctk.CTkLabel(
        metrics_frame,
        text="📊 Métricas SiPM",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    metrics_title.pack(pady=(10, 10))
    
    # Create controls frame for threshold inputs
    controls_frame = ctk.CTkFrame(metrics_frame, fg_color="#1a1a1a")
    controls_frame.pack(fill="x", padx=10, pady=(0, 15))
    
    # Load saved thresholds
    config = get_config()
    saved_thresholds = config.get_sipm_thresholds()
    
    # Amplitude threshold input
    amp_label = ctk.CTkLabel(
        controls_frame,
        text="Threshold Amplitud (mV):",
        font=ctk.CTkFont(size=11)
    )
    amp_label.pack(pady=(10, 2))
    
    amp_entry = ctk.CTkEntry(
        controls_frame,
        width=120,
        height=28,
        font=ctk.CTkFont(size=11)
    )
    amp_entry.insert(0, str(saved_thresholds['amplitude_threshold_mV']))
    amp_entry.pack(pady=(0, 10))
    
    # Time threshold input
    time_label = ctk.CTkLabel(
        controls_frame,
        text="Threshold Tiempo (µs):",
        font=ctk.CTkFont(size=11)
    )
    time_label.pack(pady=(5, 2))
    
    time_entry = ctk.CTkEntry(
        controls_frame,
        width=120,
        height=28,
        font=ctk.CTkFont(size=11)
    )
    time_entry.insert(0, str(saved_thresholds['time_threshold_us']))
    time_entry.pack(pady=(0, 10))
    
    # Update button
    update_button = ctk.CTkButton(
        controls_frame,
        text="🔄 Actualizar",
        command=on_update_button,
        width=120,
        height=32,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#2ecc71",
        hover_color="#27ae60"
    )
    update_button.pack(pady=(5, 5))
    
    # Save configuration button
    save_config_btn = ctk.CTkButton(
        controls_frame,
        text="💾 Guardar Config",
        command=on_save_config,
        width=120,
        height=28,
        font=ctk.CTkFont(size=11),
        fg_color="#3498db",
        hover_color="#2980b9"
    )
    save_config_btn.pack(pady=(0, 5))
    
    # Export button
    def on_export():
        """Export SiPM metrics."""
        from tkinter import filedialog
        from datetime import datetime
        
        # Check if metrics exist
        if metrics_widgets['metrics'] is None:
            print("Error: No hay métricas para exportar")
            return
        
        # Create custom dialog for format selection
        export_dialog = ctk.CTkToplevel(top)
        export_dialog.title("Exportar Métricas SiPM")
        export_dialog.geometry("300x150")
        export_dialog.transient(top)
        export_dialog.grab_set()
        
        # Center the dialog
        export_dialog.update_idletasks()
        x = (export_dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (export_dialog.winfo_screenheight() // 2) - (150 // 2)
        export_dialog.geometry(f"300x150+{x}+{y}")
        
        selected_format = [None]
        
        def select_format(fmt):
            selected_format[0] = fmt
            export_dialog.destroy()
        
        # Label
        label = ctk.CTkLabel(
            export_dialog,
            text="Selecciona el formato:",
            font=ctk.CTkFont(size=13)
        )
        label.pack(pady=(20, 15))
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(export_dialog, fg_color="transparent")
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
        
        # Wait for dialog
        top.wait_window(export_dialog)
        
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
        default_filename = f"sipm_metrics_{timestamp}.{file_ext}"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{file_ext}",
            filetypes=file_types,
            initialfile=default_filename,
            title="Guardar Métricas"
        )
        
        if not filepath:
            return
        
        # Get current thresholds
        try:
            amp_val = float(amp_entry.get())
            time_val = float(time_entry.get())
        except ValueError:
            amp_val = None
            time_val = None
        
        # Export
        try:
            if file_ext == "csv":
                ResultsExporter.export_sipm_metrics_to_csv(
                    metrics_widgets['metrics'], filepath, amp_val, time_val
                )
            else:
                ResultsExporter.export_sipm_metrics_to_json(
                    metrics_widgets['metrics'], filepath, amp_val, time_val
                )
            print(f"✓ Métricas exportadas a {filepath}")
        except Exception as e:
            print(f"Error exportando: {e}")
    
    export_btn = ctk.CTkButton(
        controls_frame,
        text="📊 Exportar Métricas",
        command=on_export,
        width=120,
        height=28,
        font=ctk.CTkFont(size=11),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    export_btn.pack(pady=(0, 10))
    
    # Initial plot with default thresholds
    update_plot(60.0, 1e-4)
    
    # Ensure window stays on top
    top.after(100, lambda: top.lift())
    top.after(100, lambda: top.focus_force())


def show_all_waveforms(parent, waveform_files, global_min_amp, global_max_amp):
    """
    Show all waveforms overlaid.
    
    Args:
        parent: Parent window
        waveform_files: List of waveform file paths
        global_min_amp: Global minimum amplitude
        global_max_amp: Global maximum amplitude
    """
    if not waveform_files:
        print("No hay archivos cargados.")
        return
    
    # Create window
    top = ctk.CTkToplevel(parent)
    top.title("Todas las Waveforms")
    top.geometry("1200x800")
    
    # Create frame for plot and toolbar
    plot_frame = ctk.CTkFrame(top)
    plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create plot
    fig = plt.Figure(figsize=(12, 8), dpi=100)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.08)
    
    num_files = len(waveform_files)
    print(f"Procesando {num_files} archivos...")
    
    # Determine alpha and linewidth based on file count
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
        alpha_value = 0.2
        linewidth = 1.0
    
    # Plot all waveforms
    for wf_file in waveform_files:
        try:
            with open(wf_file, 'r') as f:
                lines = f.readlines()
            
            t_half = float(lines[0].strip())
            amplitudes = np.array([float(line.strip()) for line in lines[2:] if line.strip()])
            
            t_start = t_half - (WINDOW_TIME / 2)
            t_global = t_start + (np.arange(len(amplitudes)) * SAMPLE_TIME)
            
            ax.plot(t_global * 1e6, amplitudes * 1000,
                   color=COLOR_WAVEFORM_OVERLAY,
                   alpha=alpha_value,
                   linewidth=linewidth,
                   antialiased=True,
                   rasterized=False)
        except Exception as e:
            print(f"Error procesando {wf_file}: {e}")
    
    ax.set_xlabel("Tiempo Global (µs)", fontsize=12, weight='bold')
    ax.set_ylabel("Amplitud (mV)", fontsize=12, weight='bold')
    ax.set_title(f"Todas las Waveforms Superpuestas ({num_files} archivos)",
                fontsize=14, weight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#cccccc')
    ax.set_ylim(global_min_amp * 1000, global_max_amp * 1000)
    
    # White background
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
    
    # Add navigation toolbar
    toolbar_frame = tk.Frame(plot_frame, bg='#f0f0f0')
    toolbar_frame.pack(side="top", fill="x")
    
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
    toolbar.config(background='#f0f0f0')
    toolbar._message_label.config(background='#f0f0f0', foreground='black')
    
    # Pack canvas
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    
    # Instructions
    info_label = ctk.CTkLabel(
        top,
        text="💡 Usa la barra de herramientas: 🏠 Reset | ← → Navegar | 🔍 Zoom (selecciona área) | ✋ Pan (arrastra) | 🖱️ Click derecho para alejar",
        font=ctk.CTkFont(size=10)
    )
    info_label.pack(side="bottom", pady=(0, 5))
    
    # Ensure window stays on top
    top.after(100, lambda: top.lift())
    top.after(100, lambda: top.focus_force())
