"""
Advanced SiPM analysis window with Recovery Time, Jitter, and Pulse Shape analysis.
ENHANCED VERSION with controls, additional plots, and export buttons.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime
import json
import pandas as pd

from config import SAMPLE_TIME, WINDOW_TIME, NUM_POINTS
from utils.pulse_analysis import (
    calculate_rise_time, calculate_fall_time, calculate_fwhm,
    fit_exponential_recovery, extract_pulse_template, perform_pulse_pca,
    calculate_pulse_area, fit_gaussian_jitter
)
from utils.plotting import save_figure
from views.popups.base_popup import BasePopup


def show_advanced_sipm_analysis(parent, results, waveform_data):
    """
    Show advanced SiPM analysis window with multiple analysis types.
    
    Args:
        parent: Parent window
        results: AnalysisResults object
        waveform_data: WaveformData object
    """
    if not results.accepted_results and not results.afterpulse_results:
        print("No hay datos suficientes para análisis avanzado.")
        return
    
    # Create window
    window = BasePopup(parent, "Análisis Avanzado SiPM", 1400, 800)
    
    # Create main container
    main_frame = ctk.CTkFrame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create tabview
    tabview = ctk.CTkTabview(main_frame)
    tabview.pack(fill="both", expand=True)
    
    # Add tabs
    tab_recovery = tabview.add("Recovery Time")
    tab_jitter = tabview.add("Jitter Temporal")
    tab_pulse_shape = tabview.add("Pulse Shape")
    
    # ===== TAB 1: RECOVERY TIME ANALYSIS =====
    create_recovery_time_tab(tab_recovery, results)
    
    # ===== TAB 2: JITTER TEMPORAL ANALYSIS =====
    create_jitter_tab(tab_jitter, results)
    
    # ===== TAB 3: PULSE SHAPE ANALYSIS =====
    create_pulse_shape_tab(tab_pulse_shape, results)


def create_recovery_time_tab(parent, results):
    """Create Recovery Time analysis tab."""
    # Layout: Controls | Plot | Metrics
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_columnconfigure(1, weight=3)
    parent.grid_columnconfigure(2, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    # Left: Controls
    controls_frame = ctk.CTkFrame(parent)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
    
    controls_title = ctk.CTkLabel(
        controls_frame,
        text="⚙️ Controles",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    controls_title.pack(pady=(20, 15))
    
    # Center: Plot
    plot_frame = ctk.CTkFrame(parent)
    plot_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    # Right: Metrics
    metrics_frame = ctk.CTkFrame(parent)
    metrics_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)
    
    metrics_title = ctk.CTkLabel(
        metrics_frame,
        text="📊 Resultados",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    metrics_title.pack(pady=(20, 15))
    
    # Extract recovery time data
    delta_times = []
    afterpulse_amps = []
    waveform_counts = []  # Track number of afterpulses per waveform
    
    for res in results.afterpulse_results:
        if len(res.peaks) < 2:
            continue
        
        # Get peak positions and amplitudes
        peak_positions = res.peaks
        peak_amps = res.amplitudes[peak_positions]
        
        # Main peak is typically the first or largest
        main_peak_idx = 0
        main_peak_pos = peak_positions[main_peak_idx]
        
        # Calculate time array
        time_array = np.arange(len(res.amplitudes)) * SAMPLE_TIME - (WINDOW_TIME / 2)
        main_peak_time = time_array[main_peak_pos]
        
        # Get afterpulses
        afterpulse_count = 0
        for i in range(1, len(peak_positions)):
            afterpulse_pos = peak_positions[i]
            afterpulse_time = time_array[afterpulse_pos]
            
            delta_t = afterpulse_time - main_peak_time
            if delta_t > 0:  # Only positive time differences
                delta_times.append(delta_t * 1e6)  # Convert to µs
                afterpulse_amps.append(peak_amps[i] * 1000)  # Convert to mV
                afterpulse_count += 1
        
        if afterpulse_count > 0:
            waveform_counts.append(afterpulse_count)
    
    # State for plot controls
    plot_state = {
        'fig': None,
        'ax': None,
        'canvas': None,
        'delta_times': np.array(delta_times) if delta_times else np.array([]),
        'afterpulse_amps': np.array(afterpulse_amps) if afterpulse_amps else np.array([]),
        'waveform_counts': waveform_counts,
        'show_log': False,
        'bin_count': 20
    }
    
    def update_plot():
        """Update the recovery time plot."""
        if plot_state['fig'] is None:
            plot_state['fig'] = plt.Figure(figsize=(8, 6), dpi=100)
        
        plot_state['fig'].clear()
        
        if len(plot_state['delta_times']) > 0:
            # Create 2x1 subplot
            ax1 = plot_state['fig'].add_subplot(211)
            ax2 = plot_state['fig'].add_subplot(212)
            
            delta_times = plot_state['delta_times']
            afterpulse_amps = plot_state['afterpulse_amps']
            
            # Top: Scatter plot with exponential fit
            ax1.scatter(delta_times, afterpulse_amps, alpha=0.6, s=50, 
                      color='#3498db', edgecolors='black', linewidth=0.5,
                      label='Afterpulses')
            
            # Fit exponential if enough data
            tau_result = np.nan
            A0_result = np.nan
            if len(delta_times) > 5:
                tau, A0, fitted_curve = fit_exponential_recovery(
                    delta_times / 1e6, afterpulse_amps / 1000
                )
                
                if not np.isnan(tau):
                    tau_result = tau * 1e6  # Convert to µs
                    A0_result = A0 * 1000  # Convert to mV
                    t_fit = np.linspace(np.min(delta_times), np.max(delta_times), 200)
                    y_fit = A0_result * np.exp(-t_fit / tau_result)
                    
                    ax1.plot(t_fit, y_fit, '--', linewidth=2.5, color='#e74c3c',
                           label=f'Fit: τ = {tau_result:.2f} µs')
            
            if plot_state['show_log']:
                ax1.set_yscale('log')
            
            ax1.set_xlabel("Δt desde pulso principal (µs)", fontsize=10)
            ax1.set_ylabel("Amplitud afterpulse (mV)", fontsize=10)
            ax1.set_title("Recovery Time - Amplitud vs Δt", fontsize=11, weight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='best', fontsize=9)
            
            # Bottom: Histogram of delta times
            ax2.hist(delta_times, bins=plot_state['bin_count'], alpha=0.7,
                    color='#2ecc71', edgecolor='black')
            ax2.set_xlabel("Δt (µs)", fontsize=10)
            ax2.set_ylabel("Cuentas", fontsize=10)
            ax2.set_title("Distribución de Tiempos de Afterpulse", fontsize=11, weight='bold')
            ax2.grid(True, alpha=0.3)
            
            plot_state['fig'].tight_layout()
            
            # Update metrics - clear previous stats first
            for widget in metrics_frame.winfo_children():
                if widget != metrics_title:
                    widget.destroy()
            
            # Now create new stats container
            stats_container = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            stats_container.pack(fill="both", expand=True, padx=10)
            
            def add_stat(label, value, color=None):
                frame = ctk.CTkFrame(stats_container, fg_color="#2b2b2b")
                frame.pack(fill="x", pady=5)
                
                lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11))
                lbl.pack(pady=(5, 0))
                
                val = ctk.CTkLabel(
                    frame,
                    text=value,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=color if color else "white"
                )
                val.pack(pady=(0, 5))
            
            add_stat("Waveforms c/ AP", f"{len(plot_state['waveform_counts'])}")
            add_stat("Total Afterpulses", f"{len(delta_times)}")
            add_stat("AP/Waveform", f"{np.mean(plot_state['waveform_counts']):.2f}", "#9b59b6")
            add_stat("Δt Promedio", f"{np.mean(delta_times):.2f} µs", "#3498db")
            add_stat("Δt Mediana", f"{np.median(delta_times):.2f} µs", "#2ecc71")
            add_stat("Δt Desv. Std", f"{np.std(delta_times):.2f} µs", "#95a5a6")
            
            if not np.isnan(tau_result):
                add_stat("τ Recovery", f"{tau_result:.2f} µs", "#e74c3c")
                add_stat("A₀ (Fit)", f"{A0_result:.2f} mV", "#f39c12")
            else:
                add_stat("τ Recovery", "N/A", "#95a5a6")
        else:
            ax = plot_state['fig'].add_subplot(111)
            ax.text(0.5, 0.5, "No hay suficientes afterpulses\npara análisis",
                   ha='center', va='center', fontsize=14, color='gray',
                   transform=ax.transAxes)
            ax.set_xlabel("Δt (µs)")
            ax.set_ylabel("Amplitud (mV)")
            ax.set_title("Recovery Time Analysis", fontsize=13, weight='bold')
        
        # Update canvas
        if plot_state['canvas'] is None:
            plot_state['canvas'] = FigureCanvasTkAgg(plot_state['fig'], master=plot_frame)
            plot_state['canvas'].get_tk_widget().pack(fill="both", expand=True)
            
            # Context menu
            context_menu = tk.Menu(parent, tearoff=0)
            context_menu.add_command(label="💾 Guardar PNG", 
                                    command=lambda: save_figure(plot_state['fig'], "recovery_time"))
            
            def show_context_menu(event):
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            
            plot_state['canvas'].get_tk_widget().bind("<Button-3>", show_context_menu)
        
        plot_state['canvas'].draw()
    
    # Controls
    # Log scale toggle
    def toggle_log():
        plot_state['show_log'] = not plot_state['show_log']
        log_btn.configure(text=f"Escala: {'Log' if plot_state['show_log'] else 'Linear'}")
        update_plot()
    
    log_btn = ctk.CTkButton(
        controls_frame,
        text="Escala: Linear",
        command=toggle_log,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12)
    )
    log_btn.pack(pady=10, padx=10)
    
    # Bin count slider
    bin_label = ctk.CTkLabel(
        controls_frame,
        text=f"Bins histograma: {plot_state['bin_count']}",
        font=ctk.CTkFont(size=11)
    )
    bin_label.pack(pady=(10, 5))
    
    def on_bin_change(value):
        plot_state['bin_count'] = int(value)
        bin_label.configure(text=f"Bins histograma: {plot_state['bin_count']}")
    
    bin_slider = ctk.CTkSlider(
        controls_frame,
        from_=10,
        to=50,
        number_of_steps=40,
        command=on_bin_change,
        width=140
    )
    bin_slider.set(20)
    bin_slider.pack(pady=(0, 10), padx=10)
    
    # Update button
    update_btn = ctk.CTkButton(
        controls_frame,
        text="🔄 Actualizar",
        command=update_plot,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#27ae60",
        hover_color="#229954"
    )
    update_btn.pack(pady=10, padx=10)
    
    # Export button
    def export_recovery_data():
        """Export recovery time data."""
        if len(plot_state['delta_times']) == 0:
            print("No hay datos para exportar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"recovery_time_{timestamp}.csv",
            title="Exportar Recovery Time Data"
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.json'):
                data = {
                    'delta_times_us': plot_state['delta_times'].tolist(),
                    'afterpulse_amplitudes_mV': plot_state['afterpulse_amps'].tolist(),
                    'statistics': {
                        'mean_delta_t': float(np.mean(plot_state['delta_times'])),
                        'median_delta_t': float(np.median(plot_state['delta_times'])),
                        'std_delta_t': float(np.std(plot_state['delta_times'])),
                        'total_afterpulses': len(plot_state['delta_times']),
                        'waveforms_with_afterpulses': len(plot_state['waveform_counts'])
                    }
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
            else:
                df = pd.DataFrame({
                    'delta_time_us': plot_state['delta_times'],
                    'afterpulse_amplitude_mV': plot_state['afterpulse_amps']
                })
                df.to_csv(filepath, index=False)
            
            print(f"✓ Datos exportados a {filepath}")
        except Exception as e:
            print(f"Error exportando: {e}")
    
    export_btn = ctk.CTkButton(
        controls_frame,
        text="📊 Exportar Datos",
        command=export_recovery_data,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    export_btn.pack(pady=10, padx=10)
    
    # Info label
    info_label = ctk.CTkLabel(
        controls_frame,
        text="📖 Recovery Time\n\nAnaliza el tiempo de\nrecuperación del SiPM\nmediante afterpulses.\n\nAjuste exponencial:\nA(t) = A₀·exp(-t/τ)",
        font=ctk.CTkFont(size=10),
        justify="center",
        text_color="#7f8c8d"
    )
    info_label.pack(side="bottom", pady=20, padx=10)
    
    # Initial plot
    update_plot()


def create_jitter_tab(parent, results):
    """Create Jitter Temporal analysis tab."""
    # Layout: Controls | Plot | Metrics
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_columnconfigure(1, weight=3)
    parent.grid_columnconfigure(2, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    # Left: Controls
    controls_frame = ctk.CTkFrame(parent)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
    
    controls_title = ctk.CTkLabel(
        controls_frame,
        text="⚙️ Controles",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    controls_title.pack(pady=(20, 15))
    
    # Center: Plot
    plot_frame = ctk.CTkFrame(parent)
    plot_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    # Right: Metrics
    metrics_frame = ctk.CTkFrame(parent)
    metrics_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)
    
    metrics_title = ctk.CTkLabel(
        metrics_frame,
        text="📊 Resultados",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    metrics_title.pack(pady=(20, 15))
    
    # Extract peak times and amplitudes
    peak_times = []
    peak_amplitudes = []
    
    for res in results.accepted_results:
        if len(res.peaks) > 0:
            time_array = np.arange(len(res.amplitudes)) * SAMPLE_TIME - (WINDOW_TIME / 2)
            peak_time = time_array[res.peaks[0]]
            peak_amp = res.amplitudes[res.peaks[0]]
            
            peak_times.append(peak_time * 1e6)  # Convert to µs
            peak_amplitudes.append(peak_amp * 1000)  # Convert to mV
    
    # State for plot controls
    plot_state = {
        'fig': None,
        'canvas': None,
        'peak_times': np.array(peak_times) if peak_times else np.array([]),
        'peak_amplitudes': np.array(peak_amplitudes) if peak_amplitudes else np.array([]),
        'hist_bins': 30,
        'show_scatter': True
    }
    
    def update_plot():
        """Update jitter plots."""
        if plot_state['fig'] is None:
            plot_state['fig'] = plt.Figure(figsize=(8, 6), dpi=100)
        
        plot_state['fig'].clear()
        
        if len(plot_state['peak_times']) > 0:
            peak_times = plot_state['peak_times']
            peak_amplitudes = plot_state['peak_amplitudes']
            
            if plot_state['show_scatter']:
                # 2 subplots: histogram + scatter
                ax1 = plot_state['fig'].add_subplot(211)
                ax2 = plot_state['fig'].add_subplot(212)
            else:
                # Only histogram
                ax1 = plot_state['fig'].add_subplot(111)
            
            # Top: Histogram with Gaussian fit
            n, bins, patches = ax1.hist(peak_times, bins=plot_state['hist_bins'], alpha=0.7,
                                        color='#3498db', edgecolor='black',
                                        label='Distribución')
            
            # Fit Gaussian
            mu, sigma, fwhm = fit_gaussian_jitter(peak_times)
            
            # Plot Gaussian fit
            x = np.linspace(np.min(peak_times), np.max(peak_times), 200)
            from scipy.stats import norm
            y = norm.pdf(x, mu, sigma) * len(peak_times) * (bins[1] - bins[0])
            
            ax1.plot(x, y, '--', linewidth=2.5, color='#e74c3c',
                    label=f'Fit Gaussiano\nμ={mu:.2f} µs\nσ={sigma:.3f} µs')
            
            ax1.set_xlabel("Tiempo de pico (µs)", fontsize=10)
            ax1.set_ylabel("Cuentas", fontsize=10)
            ax1.set_title("Distribución Temporal de Picos", fontsize=11, weight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='best', fontsize=9)
            
            # Bottom: Scatter plot (if enabled)
            if plot_state['show_scatter']:
                ax2.scatter(peak_times, peak_amplitudes, alpha=0.5, s=30,
                           color='#2ecc71', edgecolors='black', linewidth=0.5)
                
                ax2.set_xlabel("Tiempo de pico (µs)", fontsize=10)
                ax2.set_ylabel("Amplitud (mV)", fontsize=10)
                ax2.set_title("Amplitud vs Tiempo de Pico", fontsize=11, weight='bold')
                ax2.grid(True, alpha=0.3)
            
            plot_state['fig'].tight_layout()
            
            # Update metrics - clear previous stats first
            for widget in metrics_frame.winfo_children():
                if widget != metrics_title:
                    widget.destroy()
            
            # Now create new stats container
            stats_container = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            stats_container.pack(fill="both", expand=True, padx=10)
            
            def add_stat(label, value, color=None):
                frame = ctk.CTkFrame(stats_container, fg_color="#2b2b2b")
                frame.pack(fill="x", pady=5)
                
                lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11))
                lbl.pack(pady=(5, 0))
                
                val = ctk.CTkLabel(
                    frame,
                    text=value,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=color if color else "white"
                )
                val.pack(pady=(0, 5))
            
            add_stat("Total Eventos", f"{len(peak_times)}")
            add_stat("μ (Media)", f"{mu:.3f} µs", "#3498db")
            add_stat("σ (Desv. Std)", f"{sigma:.3f} µs", "#e74c3c")
            add_stat("FWHM", f"{fwhm:.3f} µs", "#2ecc71")
            add_stat("RMS Jitter", f"{sigma*1000:.1f} ps", "#f39c12")
            add_stat("Rango", f"{np.ptp(peak_times):.3f} µs", "#9b59b6")
        else:
            ax = plot_state['fig'].add_subplot(111)
            ax.text(0.5, 0.5, "No hay datos suficientes",
                   ha='center', va='center', fontsize=14, color='gray',
                   transform=ax.transAxes)
            ax.set_title("Jitter Temporal Analysis", fontsize=13, weight='bold')
        
        # Update canvas
        if plot_state['canvas'] is None:
            plot_state['canvas'] = FigureCanvasTkAgg(plot_state['fig'], master=plot_frame)
            plot_state['canvas'].get_tk_widget().pack(fill="both", expand=True)
            
            context_menu = tk.Menu(parent, tearoff=0)
            context_menu.add_command(label="💾 Guardar PNG", 
                                    command=lambda: save_figure(plot_state['fig'], "jitter_analysis"))
            
            def show_context_menu(event):
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            
            plot_state['canvas'].get_tk_widget().bind("<Button-3>", show_context_menu)
        
        plot_state['canvas'].draw()
    
    # Controls
    # Bins slider
    bins_label = ctk.CTkLabel(
        controls_frame,
        text=f"Bins histograma: {plot_state['hist_bins']}",
        font=ctk.CTkFont(size=11)
    )
    bins_label.pack(pady=(10, 5))
    
    def on_bins_change(value):
        plot_state['hist_bins'] = int(value)
        bins_label.configure(text=f"Bins histograma: {plot_state['hist_bins']}")
    
    bins_slider = ctk.CTkSlider(
        controls_frame,
        from_=10,
        to=60,
        number_of_steps=50,
        command=on_bins_change,
        width=140
    )
    bins_slider.set(30)
    bins_slider.pack(pady=(0, 10), padx=10)
    
    # Toggle scatter plot
    def toggle_scatter():
        plot_state['show_scatter'] = not plot_state['show_scatter']
        scatter_btn.configure(text=f"Scatter: {'ON' if plot_state['show_scatter'] else 'OFF'}")
        update_plot()
    
    scatter_btn = ctk.CTkButton(
        controls_frame,
        text="Scatter: ON",
        command=toggle_scatter,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12)
    )
    scatter_btn.pack(pady=10, padx=10)
    
    # Update button
    update_btn = ctk.CTkButton(
        controls_frame,
        text="🔄 Actualizar",
        command=update_plot,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#27ae60",
        hover_color="#229954"
    )
    update_btn.pack(pady=10, padx=10)
    
    # Export button
    def export_jitter_data():
        """Export jitter data."""
        if len(plot_state['peak_times']) == 0:
            print("No hay datos para exportar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"jitter_analysis_{timestamp}.csv",
            title="Exportar Jitter Data"
        )
        
        if not filepath:
            return
        
        try:
            mu, sigma, fwhm = fit_gaussian_jitter(plot_state['peak_times'])
            
            if filepath.endswith('.json'):
                data = {
                    'peak_times_us': plot_state['peak_times'].tolist(),
                    'peak_amplitudes_mV': plot_state['peak_amplitudes'].tolist(),
                    'statistics': {
                        'mu': float(mu),
                        'sigma': float(sigma),
                        'fwhm': float(fwhm),
                        'rms_jitter_ps': float(sigma * 1000),
                        'total_events': len(plot_state['peak_times'])
                    }
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
            else:
                df = pd.DataFrame({
                    'peak_time_us': plot_state['peak_times'],
                    'peak_amplitude_mV': plot_state['peak_amplitudes']
                })
                df.to_csv(filepath, index=False)
            
            print(f"✓ Datos exportados a {filepath}")
        except Exception as e:
            print(f"Error exportando: {e}")
    
    export_btn = ctk.CTkButton(
        controls_frame,
        text="📊 Exportar Datos",
        command=export_jitter_data,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    export_btn.pack(pady=10, padx=10)
    
    # Info label
    info_label = ctk.CTkLabel(
        controls_frame,
        text="📖 Jitter Temporal\n\nMide la resolución\ntemporal del detector.\n\nFWHM = 2.355·σ\n\nMenor jitter =\nmejor resolución",
        font=ctk.CTkFont(size=10),
        justify="center",
        text_color="#7f8c8d"
    )
    info_label.pack(side="bottom", pady=20, padx=10)
    
    # Initial plot
    update_plot()


def create_pulse_shape_tab(parent, results):
    """Create Pulse Shape analysis tab."""
    # Layout: Controls | Plot | Metrics
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_columnconfigure(1, weight=3)
    parent.grid_columnconfigure(2, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    # Left: Controls
    controls_frame = ctk.CTkFrame(parent)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
    
    controls_title = ctk.CTkLabel(
        controls_frame,
        text="⚙️ Controles",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    controls_title.pack(pady=(20, 15))
    
    # Center: Plot
    plot_frame = ctk.CTkFrame(parent)
    plot_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    # Right: Metrics
    metrics_frame = ctk.CTkFrame(parent)
    metrics_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)
    
    metrics_title = ctk.CTkLabel(
        metrics_frame,
        text="📊 Resultados",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    metrics_title.pack(pady=(20, 15))
    
    # Extract pulse shape parameters (NO AREA - removed as requested)
    rise_times = []
    fall_times = []
    fwhms = []
    rise_fall_ratios = []
    
    for res in results.accepted_results:
        if len(res.peaks) > 0:
            time_array = np.arange(len(res.amplitudes)) * SAMPLE_TIME - (WINDOW_TIME / 2)
            peak_idx = res.peaks[0]
            baseline = results.baseline_low
            
            # Calculate parameters
            rise_time = calculate_rise_time(res.amplitudes, time_array, peak_idx, baseline)
            fall_time = calculate_fall_time(res.amplitudes, time_array, peak_idx, baseline)
            fwhm = calculate_fwhm(res.amplitudes, time_array, peak_idx, baseline)
            
            if not np.isnan(rise_time):
                rise_times.append(rise_time * 1e9)  # Convert to ns
            if not np.isnan(fall_time):
                fall_times.append(fall_time * 1e9)  # Convert to ns
            if not np.isnan(fwhm):
                fwhms.append(fwhm * 1e9)  # Convert to ns
            
            # Calculate rise/fall ratio
            if not np.isnan(rise_time) and not np.isnan(fall_time) and fall_time > 0:
                rise_fall_ratios.append(rise_time / fall_time)
    
    # State for plot controls
    plot_state = {
        'fig': None,
        'canvas': None,
        'rise_times': np.array(rise_times) if rise_times else np.array([]),
        'fall_times': np.array(fall_times) if fall_times else np.array([]),
        'fwhms': np.array(fwhms) if fwhms else np.array([]),
        'rise_fall_ratios': np.array(rise_fall_ratios) if rise_fall_ratios else np.array([]),
        'hist_bins': 20,
        'show_ratio': True
    }
    
    def update_plot():
        """Update pulse shape plots."""
        if plot_state['fig'] is None:
            plot_state['fig'] = plt.Figure(figsize=(8, 6), dpi=100)
        
        plot_state['fig'].clear()
        
        if len(plot_state['rise_times']) > 0:
            if plot_state['show_ratio']:
                # 2x2 grid: rise, fall, fwhm, ratio
                ax1 = plot_state['fig'].add_subplot(221)
                ax2 = plot_state['fig'].add_subplot(222)
                ax3 = plot_state['fig'].add_subplot(223)
                ax4 = plot_state['fig'].add_subplot(224)
            else:
                # 1x3 grid: rise, fall, fwhm
                ax1 = plot_state['fig'].add_subplot(131)
                ax2 = plot_state['fig'].add_subplot(132)
                ax3 = plot_state['fig'].add_subplot(133)
            
            bins = plot_state['hist_bins']
            
            # Rise time histogram
            ax1.hist(plot_state['rise_times'], bins=bins, alpha=0.7, color='#3498db', edgecolor='black')
            ax1.set_xlabel("Rise Time (ns)", fontsize=9)
            ax1.set_ylabel("Cuentas", fontsize=9)
            ax1.set_title("Rise Time (10%-90%)", fontsize=10, weight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Fall time histogram
            ax2.hist(plot_state['fall_times'], bins=bins, alpha=0.7, color='#e74c3c', edgecolor='black')
            ax2.set_xlabel("Fall Time (ns)", fontsize=9)
            ax2.set_ylabel("Cuentas", fontsize=9)
            ax2.set_title("Fall Time (90%-10%)", fontsize=10, weight='bold')
            ax2.grid(True, alpha=0.3)
            
            # FWHM histogram
            ax3.hist(plot_state['fwhms'], bins=bins, alpha=0.7, color='#2ecc71', edgecolor='black')
            ax3.set_xlabel("FWHM (ns)", fontsize=9)
            ax3.set_ylabel("Cuentas", fontsize=9)
            ax3.set_title("Full Width Half Maximum", fontsize=10, weight='bold')
            ax3.grid(True, alpha=0.3)
            
            # Rise/Fall ratio (if enabled)
            if plot_state['show_ratio'] and len(plot_state['rise_fall_ratios']) > 0:
                ax4.hist(plot_state['rise_fall_ratios'], bins=bins, alpha=0.7, color='#9b59b6', edgecolor='black')
                ax4.set_xlabel("Rise/Fall Ratio", fontsize=9)
                ax4.set_ylabel("Cuentas", fontsize=9)
                ax4.set_title("Ratio Rise/Fall Time", fontsize=10, weight='bold')
                ax4.grid(True, alpha=0.3)
            
            plot_state['fig'].tight_layout()
            
            # Update metrics - clear previous stats first
            for widget in metrics_frame.winfo_children():
                if widget != metrics_title:
                    widget.destroy()
            
            # Now create new stats container
            stats_container = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            stats_container.pack(fill="both", expand=True, padx=10)
            
            def add_stat(label, value, color=None):
                frame = ctk.CTkFrame(stats_container, fg_color="#2b2b2b")
                frame.pack(fill="x", pady=4)
                
                lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=10))
                lbl.pack(pady=(4, 0))
                
                val = ctk.CTkLabel(
                    frame,
                    text=value,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=color if color else "white"
                )
                val.pack(pady=(0, 4))
            
            add_stat("Total Pulsos", f"{len(plot_state['rise_times'])}")
            add_stat("Rise Time", f"{np.mean(plot_state['rise_times']):.2f} ± {np.std(plot_state['rise_times']):.2f} ns", "#3498db")
            add_stat("Fall Time", f"{np.mean(plot_state['fall_times']):.2f} ± {np.std(plot_state['fall_times']):.2f} ns", "#e74c3c")
            add_stat("FWHM", f"{np.mean(plot_state['fwhms']):.2f} ± {np.std(plot_state['fwhms']):.2f} ns", "#2ecc71")
            
            if len(plot_state['rise_fall_ratios']) > 0:
                add_stat("Ratio R/F", f"{np.mean(plot_state['rise_fall_ratios']):.3f} ± {np.std(plot_state['rise_fall_ratios']):.3f}", "#9b59b6")
        else:
            ax = plot_state['fig'].add_subplot(111)
            ax.text(0.5, 0.5, "No hay datos suficientes",
                   ha='center', va='center', fontsize=14, color='gray',
                   transform=ax.transAxes)
            ax.set_title("Pulse Shape Analysis", fontsize=13, weight='bold')
        
        # Update canvas
        if plot_state['canvas'] is None:
            plot_state['canvas'] = FigureCanvasTkAgg(plot_state['fig'], master=plot_frame)
            plot_state['canvas'].get_tk_widget().pack(fill="both", expand=True)
            
            context_menu = tk.Menu(parent, tearoff=0)
            context_menu.add_command(label="💾 Guardar PNG", 
                                    command=lambda: save_figure(plot_state['fig'], "pulse_shape"))
            
            def show_context_menu(event):
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            
            plot_state['canvas'].get_tk_widget().bind("<Button-3>", show_context_menu)
        
        plot_state['canvas'].draw()
    
    # Controls
    # Bins slider
    bins_label = ctk.CTkLabel(
        controls_frame,
        text=f"Bins histograma: {plot_state['hist_bins']}",
        font=ctk.CTkFont(size=11)
    )
    bins_label.pack(pady=(10, 5))
    
    def on_bins_change(value):
        plot_state['hist_bins'] = int(value)
        bins_label.configure(text=f"Bins histograma: {plot_state['hist_bins']}")
    
    bins_slider = ctk.CTkSlider(
        controls_frame,
        from_=10,
        to=40,
        number_of_steps=30,
        command=on_bins_change,
        width=140
    )
    bins_slider.set(20)
    bins_slider.pack(pady=(0, 10), padx=10)
    
    # Toggle ratio plot
    def toggle_ratio():
        plot_state['show_ratio'] = not plot_state['show_ratio']
        ratio_btn.configure(text=f"Ratio Plot: {'ON' if plot_state['show_ratio'] else 'OFF'}")
        update_plot()
    
    ratio_btn = ctk.CTkButton(
        controls_frame,
        text="Ratio Plot: ON",
        command=toggle_ratio,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12)
    )
    ratio_btn.pack(pady=10, padx=10)
    
    # Update button
    update_btn = ctk.CTkButton(
        controls_frame,
        text="🔄 Actualizar",
        command=update_plot,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#27ae60",
        hover_color="#229954"
    )
    update_btn.pack(pady=10, padx=10)
    
    # Export button
    def export_pulse_shape_data():
        """Export pulse shape data."""
        if len(plot_state['rise_times']) == 0:
            print("No hay datos para exportar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"pulse_shape_{timestamp}.csv",
            title="Exportar Pulse Shape Data"
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.json'):
                data = {
                    'rise_times_ns': plot_state['rise_times'].tolist(),
                    'fall_times_ns': plot_state['fall_times'].tolist(),
                    'fwhm_ns': plot_state['fwhms'].tolist(),
                    'rise_fall_ratios': plot_state['rise_fall_ratios'].tolist() if len(plot_state['rise_fall_ratios']) > 0 else [],
                    'statistics': {
                        'mean_rise_time': float(np.mean(plot_state['rise_times'])),
                        'std_rise_time': float(np.std(plot_state['rise_times'])),
                        'mean_fall_time': float(np.mean(plot_state['fall_times'])),
                        'std_fall_time': float(np.std(plot_state['fall_times'])),
                        'mean_fwhm': float(np.mean(plot_state['fwhms'])),
                        'std_fwhm': float(np.std(plot_state['fwhms'])),
                        'total_pulses': len(plot_state['rise_times'])
                    }
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
            else:
                # Create DataFrame with all available data
                max_len = max(len(plot_state['rise_times']), len(plot_state['fall_times']), 
                             len(plot_state['fwhms']), len(plot_state['rise_fall_ratios']))
                
                df_data = {}
                if len(plot_state['rise_times']) > 0:
                    df_data['rise_time_ns'] = plot_state['rise_times']
                if len(plot_state['fall_times']) > 0:
                    df_data['fall_time_ns'] = plot_state['fall_times']
                if len(plot_state['fwhms']) > 0:
                    df_data['fwhm_ns'] = plot_state['fwhms']
                if len(plot_state['rise_fall_ratios']) > 0:
                    df_data['rise_fall_ratio'] = plot_state['rise_fall_ratios']
                
                df = pd.DataFrame(df_data)
                df.to_csv(filepath, index=False)
            
            print(f"✓ Datos exportados a {filepath}")
        except Exception as e:
            print(f"Error exportando: {e}")
    
    export_btn = ctk.CTkButton(
        controls_frame,
        text="📊 Exportar Datos",
        command=export_pulse_shape_data,
        width=140,
        height=35,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    export_btn.pack(pady=10, padx=10)
    
    # Info label
    info_label = ctk.CTkLabel(
        controls_frame,
        text="📖 Pulse Shape\n\nCaracteriza la forma\ndel pulso SiPM.\n\nRise/Fall time:\nVelocidad de subida/bajada\n\nFWHM:\nAncho del pulso",
        font=ctk.CTkFont(size=10),
        justify="center",
        text_color="#7f8c8d"
    )
    info_label.pack(side="bottom", pady=20, padx=10)
    
    # Initial plot
    update_plot()
