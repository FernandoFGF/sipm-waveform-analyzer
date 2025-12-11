"""
Charge histogram analysis window.
"""
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.stats import norm

from config import SAMPLE_TIME
from utils import ResultsExporter
from utils.plotting import save_figure
from views.popups.base_popup import BasePopup

def show_charge_histogram(parent, accepted_results, baseline_high):
    """
    Show charge histogram of accepted peaks with multi-Gaussian fitting.
    
    Args:
        parent: Parent window
        accepted_results: List of accepted results
        baseline_high: Threshold for integral calculation
    """
    if not accepted_results:
        return
    
    # Create window
    window = BasePopup(parent, "Histograma de Carga", 1200, 700)
    
    # Create main frame with three columns
    main_frame = ctk.CTkFrame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=1)  # Controls
    main_frame.grid_columnconfigure(1, weight=3)  # Plot
    main_frame.grid_columnconfigure(2, weight=1)  # Metrics
    main_frame.grid_rowconfigure(0, weight=1)
    
    # Left: Controls panel
    controls_frame = ctk.CTkFrame(main_frame)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    
    # Center: Plot
    plot_frame = ctk.CTkFrame(main_frame)
    plot_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    
    # Right: Metrics panel
    metrics_frame = ctk.CTkFrame(main_frame)
    metrics_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
    
    # Calculate charges
    charges = []
    
    for res in accepted_results:
        # Calculate integral above baseline
        signal_above_baseline = res.amplitudes[res.amplitudes > baseline_high] - baseline_high
        
        if len(signal_above_baseline) > 0:
            charge = np.sum(signal_above_baseline) * SAMPLE_TIME
            charges.append(charge)
            
    if not charges:
        print("No hay carga calculable.")
        window.destroy()
        return
        
    charges = np.array(charges)
    # Convert to nV*s for display (typical SiPM units)
    charges_plot = charges * 1e9  # V*s -> nV*s
    
    # Store plot elements
    plot_state = {
        'fig': None,
        'ax': None,
        'canvas': None,
        'n': None,
        'bins': None
    }
    
    # Controls Panel
    controls_title = ctk.CTkLabel(
        controls_frame,
        text="⚙️ Controles de Fit",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    controls_title.pack(pady=(20, 15))
    
    # First peak approximation input
    peak_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    peak_frame.pack(fill="x", padx=10, pady=10)
    
    peak_label = ctk.CTkLabel(
        peak_frame,
        text="Primer pico (nV·s):",
        font=ctk.CTkFont(size=12)
    )
    peak_label.pack(pady=(5, 5))
    
    # Calculate initial guess as the mean
    initial_peak = np.mean(charges_plot)
    
    peak_entry = ctk.CTkEntry(
        peak_frame,
        width=150,
        height=35,
        font=ctk.CTkFont(size=14),
        justify="center"
    )
    peak_entry.insert(0, f"{initial_peak:.1f}")
    peak_entry.pack(pady=(0, 5))
    
    # Additional Gaussians slider
    slider_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    slider_frame.pack(fill="x", padx=10, pady=10)
    
    slider_label = ctk.CTkLabel(
        slider_frame,
        text="Gaussianas adicionales:",
        font=ctk.CTkFont(size=12)
    )
    slider_label.pack(pady=(5, 5))
    
    slider_value_label = ctk.CTkLabel(
        slider_frame,
        text="0",
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color="#3498db"
    )
    slider_value_label.pack(pady=(0, 5))
    
    def on_slider_change(value):
        slider_value_label.configure(text=str(int(value)))
    
    gaussians_slider = ctk.CTkSlider(
        slider_frame,
        from_=0,
        to=3,
        number_of_steps=3,
        width=150,
        command=on_slider_change
    )
    gaussians_slider.set(0)
    gaussians_slider.pack(pady=(0, 5))
    
    # Update button
    def update_plot():
        """Update the plot with new fitting parameters."""
        try:
            first_peak = float(peak_entry.get())
            num_additional = int(gaussians_slider.get())
            
            # Clear previous plot
            if plot_state['ax'] is not None:
                plot_state['ax'].clear()
            else:
                plot_state['fig'] = plt.Figure(figsize=(8, 6), dpi=100)
                plot_state['ax'] = plot_state['fig'].add_subplot(111)
            
            ax = plot_state['ax']
            
            # Histogram (use linear scale for better visualization of fits)
            n, bins, patches = ax.hist(charges_plot, bins=50, alpha=0.7, 
                                      color='#3498db', edgecolor='black', 
                                      label='Data')
            plot_state['n'] = n
            plot_state['bins'] = bins
            
            # Find peaks and fit Gaussians
            from scipy.signal import find_peaks
            from scipy.optimize import curve_fit
            
            # Get bin centers
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            # Find local maxima in the histogram (more sensitive)
            # Use a lower threshold to find more peaks
            peaks_idx, properties = find_peaks(n, height=np.max(n) * 0.02, distance=2, prominence=np.max(n) * 0.01)
            
            if len(peaks_idx) == 0:
                # No peaks found, use the specified value
                idx_first = np.argmin(np.abs(bin_centers - first_peak))
                selected_peaks = [idx_first]
                
                # If additional peaks requested, create them at expected positions
                if num_additional > 0:
                    # Assume peaks are evenly spaced (typical for SiPM multi-photon peaks)
                    for i in range(1, num_additional + 1):
                        expected_position = first_peak * (i + 1)  # 2x, 3x, 4x the first peak
                        idx_expected = np.argmin(np.abs(bin_centers - expected_position))
                        if idx_expected < len(bin_centers):
                            selected_peaks.append(idx_expected)
            else:
                # Find the first peak near the specified value
                distances = np.abs(bin_centers[peaks_idx] - first_peak)
                first_peak_idx = peaks_idx[np.argmin(distances)]
                
                # Get the position of this peak in the bin_centers array
                first_peak_position = bin_centers[first_peak_idx]
                
                # Now find additional peaks AFTER this first peak
                # Sort peaks by their position (left to right)
                sorted_by_position = sorted(zip(bin_centers[peaks_idx], peaks_idx))
                
                # Select the first peak and then the next ones after it
                selected_peaks = [first_peak_idx]
                
                if num_additional > 0:
                    # Find peaks that come after the first peak
                    peaks_after_first = [idx for pos, idx in sorted_by_position if pos > first_peak_position]
                    
                    # Add detected peaks first
                    num_detected = min(num_additional, len(peaks_after_first))
                    for i in range(num_detected):
                        selected_peaks.append(peaks_after_first[i])
                    
                    # If we still need more peaks, create them at expected positions
                    if num_detected < num_additional:
                        for i in range(num_detected + 1, num_additional + 1):
                            expected_position = first_peak_position * (i + 1)
                            idx_expected = np.argmin(np.abs(bin_centers - expected_position))
                            if idx_expected < len(bin_centers) and idx_expected not in selected_peaks:
                                selected_peaks.append(idx_expected)
            
            # Fit each Gaussian
            colors = ['#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            xmin, xmax = ax.get_xlim()
            x = np.linspace(xmin, xmax, 500)
            
            fit_results = []
            
            for i, peak_idx in enumerate(selected_peaks):
                # Initial parameters for this peak
                mu_init = bin_centers[peak_idx]
                amp_init = n[peak_idx]
                
                # Better estimate for sigma based on the peak width
                # Use a fraction of the distance to the next peak or a default value
                if i < len(selected_peaks) - 1:
                    next_peak_pos = bin_centers[selected_peaks[i+1]]
                    std_init = abs(next_peak_pos - mu_init) / 3
                else:
                    std_init = np.std(charges_plot) / (len(selected_peaks) + 1)
                
                # Define Gaussian function
                def gaussian(x, amp, mu, sigma):
                    return amp * np.exp(-(x - mu)**2 / (2 * sigma**2))
                
                # Fit around this peak
                try:
                    # Define fitting window
                    window = max(3 * std_init, (xmax - xmin) / 20)  # At least 5% of the range
                    mask = (bin_centers >= mu_init - window) & (bin_centers <= mu_init + window)
                    
                    if np.sum(mask) > 3:  # Need at least 3 points
                        popt, pcov = curve_fit(
                            gaussian,
                            bin_centers[mask],
                            n[mask],
                            p0=[amp_init, mu_init, std_init],
                            maxfev=10000,
                            bounds=([0, mu_init - window, std_init/10], 
                                   [amp_init * 2, mu_init + window, window])
                        )
                        
                        amp, mu, sigma = popt
                        
                        # Plot the fit
                        y_fit = gaussian(x, amp, mu, sigma)
                        ax.plot(x, y_fit, '--', linewidth=2.5, 
                               color=colors[i % len(colors)],
                               label=f'Pico {i+1}: μ={mu:.1f}, σ={sigma:.1f}')
                        
                        fit_results.append({'peak': i+1, 'mu': mu, 'sigma': sigma, 'amp': amp})
                except Exception as e:
                    pass  # Silently skip failed fits
            
            ax.set_xlabel(r"Carga (nV$\cdot$s)", fontsize=10)
            ax.set_ylabel("Cuentas", fontsize=10)
            ax.set_title("Histograma de Carga (Integral sobre Baseline)", fontsize=12, weight='bold')
            ax.grid(True, which="both", ls="-", alpha=0.2)
            ax.legend(loc='best', fontsize=8)
            
            # Update canvas
            if plot_state['canvas'] is None:
                plot_state['canvas'] = FigureCanvasTkAgg(plot_state['fig'], master=plot_frame)
                plot_state['canvas'].get_tk_widget().pack(fill="both", expand=True)
                # Attach context menu
                plot_state['canvas'].get_tk_widget().bind("<Button-3>", show_context_menu)
            
            plot_state['canvas'].draw()
            
            # Update metrics
            update_metrics(fit_results)
            
        except ValueError:
            print("Error: Valor inválido para el primer pico")
    
    update_btn = ctk.CTkButton(
        controls_frame,
        text="Actualizar",
        command=update_plot,
        width=150,
        height=40,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="#27ae60",
        hover_color="#229954"
    )
    update_btn.pack(pady=20)
    
    # Info label
    info_label = ctk.CTkLabel(
        controls_frame,
        text="💡 Ajusta el valor del\nprimer pico y el número\nde gaussianas adicionales.\nLuego presiona Actualizar.",
        font=ctk.CTkFont(size=10),
        text_color="#7f8c8d",
        justify="center"
    )
    info_label.pack(pady=(10, 20))
    
    # Context menu for plot (will be attached after first plot creation)
    context_menu = tk.Menu(window, tearoff=0)
    
    def save_plot_handler(fmt):
        if plot_state['fig'] is not None:
            save_figure(plot_state['fig'], default_prefix="charge_hist")
    
    context_menu.add_command(label="💾 Guardar como PNG", command=lambda: save_plot_handler("png"))
    context_menu.add_command(label="💾 Guardar como PDF", command=lambda: save_plot_handler("pdf"))
    context_menu.add_command(label="💾 Guardar como SVG", command=lambda: save_plot_handler("svg"))
    
    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    
    # Metrics Panel
    metrics_title = ctk.CTkLabel(
        metrics_frame,
        text="📊 Estadísticas",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    metrics_title.pack(pady=(20, 15))
    
    # Stats container (will be updated dynamically)
    stats_container = ctk.CTkFrame(metrics_frame, fg_color="transparent")
    stats_container.pack(fill="both", expand=True, padx=10)
    
    def update_metrics(fit_results):
        """Update metrics panel with fit results."""
        # Clear previous stats
        for widget in stats_container.winfo_children():
            widget.destroy()
        
        # Basic stats
        def add_stat(label, value, color=None):
            frame = ctk.CTkFrame(stats_container, fg_color="#2b2b2b")
            frame.pack(fill="x", pady=5)
            
            lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11))
            lbl.pack(pady=(5, 0))
            
            val = ctk.CTkLabel(
                frame,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color if color else "white"
            )
            val.pack(pady=(0, 5))
        
        add_stat("Total Eventos", f"{len(charges_plot):,}")
        add_stat("Media Global", f"{np.mean(charges_plot):.2f} nV·s", "#3498db")
        add_stat("Desv. Std Global", f"{np.std(charges_plot):.2f} nV·s", "#e74c3c")
        
        # Fit results
        if fit_results:
            separator = ctk.CTkFrame(stats_container, height=2, fg_color="#34495e")
            separator.pack(fill="x", pady=10)
            
            fits_label = ctk.CTkLabel(
                stats_container,
                text="Picos Encontrados:",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            fits_label.pack(pady=(5, 10))
            
            colors = ['#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            for result in fit_results:
                add_stat(
                    f"Pico {result['peak']}",
                    f"μ={result['mu']:.1f}\nσ={result['sigma']:.1f}",
                    colors[(result['peak']-1) % len(colors)]
                )
    
    # Initial plot
    update_plot()
    
    # Export button
    def on_export():
        """Export charge data."""
        from tkinter import filedialog
        from datetime import datetime
        import pandas as pd
        import json
        
        # Create custom dialog for format selection
        export_dialog = ctk.CTkToplevel(window)
        export_dialog.title("Exportar Datos de Carga")
        export_dialog.geometry("300x150")
        export_dialog.transient(window)
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
        window.wait_window(export_dialog)
        
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
        default_filename = f"charge_data_{timestamp}.{file_ext}"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{file_ext}",
            filetypes=file_types,
            initialfile=default_filename,
            title="Guardar Datos de Carga"
        )
        
        if not filepath:
            return
            
        try:
            if file_ext == "csv":
                df = pd.DataFrame({'charge_mV_ns': charges_plot})
                df.to_csv(filepath, index=False)
            else:
                data = {
                    'charge_mV_ns': charges_plot.tolist(),
                    'stats': {
                        'mean': float(np.mean(charges_plot)),
                        'std': float(np.std(charges_plot)),
                        'min': float(np.min(charges_plot)),
                        'max': float(np.max(charges_plot)),
                        'count': len(charges_plot)
                    }
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
            print(f"[OK] Datos exportados a {filepath}")
        except Exception as e:
            print(f"Error exportando: {e}")

    export_btn = ctk.CTkButton(
        metrics_frame,
        text="📊 Exportar Datos",
        command=on_export,
        width=120,
        height=40,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    export_btn.pack(side="bottom", pady=20, padx=20)

