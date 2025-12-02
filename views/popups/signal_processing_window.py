"""
Signal processing window with filter preview - SIMPLIFIED VERSION
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import SAMPLE_TIME
from utils.signal_filters import apply_savitzky_golay, calculate_snr_improvement, calculate_rms_noise
from views.popups.base_popup import BasePopup


def show_signal_processing(parent, waveform_data, current_results):
    """Show signal processing window with filter preview."""
    if not waveform_data or not waveform_data.waveform_files:
        print("No waveform data available")
        return
    
    # Create window
    window = BasePopup(parent, "Procesamiento de Señal - Smoothing", 1200, 600)
    
    # Create main frame with three columns
    main_frame = ctk.CTkFrame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=1)  # Controls
    main_frame.grid_columnconfigure(1, weight=2)  # Original view
    main_frame.grid_columnconfigure(2, weight=2)  # Filtered view
    main_frame.grid_rowconfigure(0, weight=1)
    
    # Left: Controls panel
    controls_frame = ctk.CTkFrame(main_frame)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    
    # Center: Original plot
    original_frame = ctk.CTkFrame(main_frame)
    original_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    
    # Right: Filtered plot
    filtered_frame = ctk.CTkFrame(main_frame)
    filtered_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
    
    # State variables
    state = {
        'current_idx': 0,
        'total_waveforms': len(waveform_data.waveform_files),
        'original_canvas': None,
        'filtered_canvas': None,
        'original_fig': None,
        'filtered_fig': None,
        'current_filter': 'Smoothing'
    }
    
    # Parameter widgets storage
    param_widgets = {}
    
    # ===== CONTROLS PANEL =====
    controls_title = ctk.CTkLabel(
        controls_frame,
        text="⚙️ Filtros de Señal",
        font=ctk.CTkFont(size=14, weight="bold")
    )
    controls_title.pack(pady=(15, 10))
    
    # Filter selector
    filter_label = ctk.CTkLabel(
        controls_frame,
        text="Tipo de Filtro:",
        font=ctk.CTkFont(size=11)
    )
    filter_label.pack(pady=(5, 2))
    
    filter_var = ctk.StringVar(value="Smoothing")
    
    def on_filter_change(choice):
        state['current_filter'] = choice
        create_filter_params(choice)
    
    filter_selector = ctk.CTkOptionMenu(
        controls_frame,
        values=["Smoothing", "Decimation"],
        variable=filter_var,
        width=170,
        height=32,
        font=ctk.CTkFont(size=11),
        command=on_filter_change
    )
    filter_selector.pack(pady=(0, 10))
    
    # Description label (will be updated)
    desc_label = ctk.CTkLabel(
        controls_frame,
        text="",
        font=ctk.CTkFont(size=9),
        text_color="#7f8c8d",
        wraplength=170
    )
    desc_label.pack(pady=(0, 10))
    
    # Parameters frame (dynamic)
    params_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    params_frame.pack(fill="x", padx=10, pady=5)
    
    def clear_params():
        """Clear parameter widgets."""
        for widget in params_frame.winfo_children():
            widget.destroy()
        param_widgets.clear()
    
    def create_filter_params(filter_name):
        """Create parameter controls based on selected filter."""
        clear_params()
        
        if filter_name == "Smoothing":
            desc_label.configure(text="Suaviza la señal reduciendo\nruido de alta frecuencia")
            
            window_label = ctk.CTkLabel(params_frame, text="Window Length:", font=ctk.CTkFont(size=10))
            window_label.pack(pady=(5, 2))
            window_value = ctk.CTkLabel(params_frame, text="11", font=ctk.CTkFont(size=14, weight="bold"))
            window_value.pack()
            def on_window_change(val):
                val = int(val)
                if val % 2 == 0:
                    val += 1
                window_value.configure(text=str(val))
            # Increased range: 5-101 (was 5-51) for more aggressive smoothing
            window_slider = ctk.CTkSlider(params_frame, from_=5, to=101, number_of_steps=48, command=on_window_change, width=150)
            window_slider.set(11)
            window_slider.pack(pady=(0, 10))
            
            poly_label = ctk.CTkLabel(params_frame, text="Poly Order:", font=ctk.CTkFont(size=10))
            poly_label.pack(pady=(5, 2))
            poly_value = ctk.CTkLabel(params_frame, text="3", font=ctk.CTkFont(size=14, weight="bold"))
            poly_value.pack()
            # Increased range: 1-7 (was 1-5) for more flexibility
            poly_slider = ctk.CTkSlider(params_frame, from_=1, to=7, number_of_steps=6, command=lambda val: poly_value.configure(text=str(int(val))), width=150)
            poly_slider.set(3)
            poly_slider.pack(pady=(0, 10))
            
            param_widgets['window_slider'] = window_slider
            param_widgets['poly_slider'] = poly_slider
            
        elif filter_name == "Decimation":
            desc_label.configure(text="Reduce puntos de datos\n(archivos más pequeños)")
            
            factor_label = ctk.CTkLabel(params_frame, text="Factor de Decimación:", font=ctk.CTkFont(size=10))
            factor_label.pack(pady=(5, 2))
            factor_value = ctk.CTkLabel(params_frame, text="2", font=ctk.CTkFont(size=14, weight="bold"))
            factor_value.pack()
            
            # Info label showing reduction
            info_label = ctk.CTkLabel(
                params_frame,
                text="Factor 2 = 50% puntos\nFactor 10 = 10% puntos\n\nEl SAMPLE_TIME se ajusta\nautomáticamente al cargar.",
                font=ctk.CTkFont(size=8),
                text_color="#7f8c8d",
                justify="center"
            )
            info_label.pack(pady=(0, 5))
            
            factor_slider = ctk.CTkSlider(params_frame, from_=2, to=10, number_of_steps=8, command=lambda val: factor_value.configure(text=str(int(val))), width=150)
            factor_slider.set(2)
            factor_slider.pack(pady=(0, 10))
            
            param_widgets['factor_slider'] = factor_slider
    
    # Initialize with Smoothing params
    create_filter_params("Smoothing")
    
    # Navigation
    nav_label = ctk.CTkLabel(controls_frame, text="Navegación:", font=ctk.CTkFont(size=11, weight="bold"))
    nav_label.pack(pady=(10, 5))
    
    current_label = ctk.CTkLabel(controls_frame, text=f"1 / {state['total_waveforms']}", font=ctk.CTkFont(size=12))
    current_label.pack(pady=5)
    
    nav_buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    nav_buttons_frame.pack(pady=5)
    
    # Filename label
    filename_label = ctk.CTkLabel(
        controls_frame,
        text="",
        font=ctk.CTkFont(size=8),
        text_color="#7f8c8d",
        wraplength=160
    )
    filename_label.pack(pady=(5, 15))
    
    # Metrics
    metrics_frame = ctk.CTkFrame(controls_frame, fg_color="#2b2b2b")
    metrics_frame.pack(fill="x", padx=10, pady=10)
    
    metrics_title = ctk.CTkLabel(metrics_frame, text="📊 Métricas", font=ctk.CTkFont(size=11, weight="bold"))
    metrics_title.pack(pady=(8, 5))
    
    snr_label = ctk.CTkLabel(metrics_frame, text="SNR: -- dB", font=ctk.CTkFont(size=10))
    snr_label.pack(pady=2)
    
    rms_before_label = ctk.CTkLabel(metrics_frame, text="RMS antes: --", font=ctk.CTkFont(size=9), text_color="#7f8c8d")
    rms_before_label.pack(pady=1)
    
    rms_after_label = ctk.CTkLabel(metrics_frame, text="RMS después: --", font=ctk.CTkFont(size=9), text_color="#7f8c8d")
    rms_after_label.pack(pady=(1, 8))
    
    # ===== PLOT FUNCTIONS =====
    def apply_current_filter(amplitudes):
        """Apply the currently selected filter."""
        filter_name = state['current_filter']
        
        if filter_name == "Smoothing":
            window = int(param_widgets['window_slider'].get())
            poly = int(param_widgets['poly_slider'].get())
            return apply_savitzky_golay(amplitudes, window, poly)
            
        elif filter_name == "Decimation":
            from scipy.signal import decimate
            factor = int(param_widgets['factor_slider'].get())
            # Decimate without interpolating back - this reduces file size
            filtered = decimate(amplitudes, factor, zero_phase=True)
            return filtered
        
        return amplitudes.copy()
    
    def update_plots():
        """Update both original and filtered plots."""
        idx = state['current_idx']
        wf_path = waveform_data.waveform_files[idx]
        
        # Read waveform data
        from utils.file_io import read_waveform_file
        try:
            t_half, amplitudes = read_waveform_file(wf_path)
        except Exception as e:
            print(f"Error reading waveform: {e}")
            return
        
        times = np.arange(len(amplitudes)) * SAMPLE_TIME * 1e6  # Convert to µs
        
        # Apply filter
        filtered_amps = apply_current_filter(amplitudes)
        
        # Create time array for filtered signal (may be different length for decimation)
        times_filtered = np.arange(len(filtered_amps)) * SAMPLE_TIME * 1e6
        if state['current_filter'] == "Decimation":
            # Adjust time scale for decimated signal
            factor = int(param_widgets['factor_slider'].get())
            times_filtered = np.arange(len(filtered_amps)) * SAMPLE_TIME * factor * 1e6
        
        # Convert to mV
        amps_mv = amplitudes * 1000
        filtered_mv = filtered_amps * 1000
        
        # Update labels
        filename_label.configure(text=wf_path.name)
        current_label.configure(text=f"{idx + 1} / {state['total_waveforms']}")
        
        # Calculate metrics
        snr_improvement = calculate_snr_improvement(amplitudes, filtered_amps)
        rms_before = calculate_rms_noise(amplitudes) * 1000
        rms_after = calculate_rms_noise(filtered_amps) * 1000
        
        snr_label.configure(text=f"SNR: {snr_improvement:+.2f} dB")
        rms_before_label.configure(text=f"RMS antes: {rms_before:.3f} mV")
        rms_after_label.configure(text=f"RMS después: {rms_after:.3f} mV")
        
        # Plot original
        if state['original_fig'] is None:
            state['original_fig'] = plt.Figure(figsize=(5, 4), dpi=100)
            state['original_ax'] = state['original_fig'].add_subplot(111)
        
        ax_orig = state['original_ax']
        ax_orig.clear()
        ax_orig.plot(times, amps_mv, linewidth=0.8, color='#3498db')
        ax_orig.set_xlabel("Tiempo (µs)", fontsize=9)
        ax_orig.set_ylabel("Amplitud (mV)", fontsize=9)
        ax_orig.set_title("Original", fontsize=11, weight='bold')
        ax_orig.grid(True, alpha=0.3)
        ax_orig.tick_params(labelsize=8)
        
        if state['original_canvas'] is None:
            state['original_canvas'] = FigureCanvasTkAgg(state['original_fig'], master=original_frame)
            state['original_canvas'].get_tk_widget().pack(fill="both", expand=True)
        
        state['original_canvas'].draw()
        state['original_canvas'].flush_events()
        
        # Plot filtered
        if state['filtered_fig'] is None:
            state['filtered_fig'] = plt.Figure(figsize=(5, 4), dpi=100)
            state['filtered_ax'] = state['filtered_fig'].add_subplot(111)
        
        ax_filt = state['filtered_ax']
        ax_filt.clear()
        ax_filt.plot(times_filtered, filtered_mv, linewidth=0.8, color='#27ae60')
        ax_filt.set_xlabel("Tiempo (µs)", fontsize=9)
        ax_filt.set_ylabel("Amplitud (mV)", fontsize=9)
        ax_filt.set_title(f"Filtrado ({state['current_filter']})", fontsize=11, weight='bold')
        ax_filt.grid(True, alpha=0.3)
        ax_filt.tick_params(labelsize=8)
        
        # Match y-axis limits
        y_min = min(ax_orig.get_ylim()[0], ax_filt.get_ylim()[0])
        y_max = max(ax_orig.get_ylim()[1], ax_filt.get_ylim()[1])
        ax_orig.set_ylim(y_min, y_max)
        ax_filt.set_ylim(y_min, y_max)
        
        if state['filtered_canvas'] is None:
            state['filtered_canvas'] = FigureCanvasTkAgg(state['filtered_fig'], master=filtered_frame)
            state['filtered_canvas'].get_tk_widget().pack(fill="both", expand=True)
        
        state['filtered_canvas'].draw()
        state['filtered_canvas'].flush_events()
    
    def navigate_prev():
        if state['current_idx'] > 0:
            state['current_idx'] -= 1
            update_plots()
    
    def navigate_next():
        if state['current_idx'] < state['total_waveforms'] - 1:
            state['current_idx'] += 1
            update_plots()
    
    prev_btn = ctk.CTkButton(nav_buttons_frame, text="◄", command=navigate_prev, width=50, height=30, font=ctk.CTkFont(size=14))
    prev_btn.pack(side="left", padx=3)
    
    next_btn = ctk.CTkButton(nav_buttons_frame, text="►", command=navigate_next, width=50, height=30, font=ctk.CTkFont(size=14))
    next_btn.pack(side="left", padx=3)
    
    # Update button
    update_btn = ctk.CTkButton(
        controls_frame,
        text="Actualizar Preview",
        command=update_plots,
        width=160,
        height=35,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color="#27ae60",
        hover_color="#229954"
    )
    update_btn.pack(pady=15)
    
    # Apply to all button
    def apply_to_all():
        """Apply filter to all waveforms and save to new directory."""
        from pathlib import Path
        from tkinter import messagebox
        import os
        
        # Get filter name and parameters
        filter_name = state['current_filter']
        
        # Create new directory name based on filter
        original_dir = waveform_data.data_dir
        if filter_name == "Smoothing":
            window = int(param_widgets['window_slider'].get())
            poly = int(param_widgets['poly_slider'].get())
            new_dir_name = f"{original_dir.name}_{filter_name}_w{window}_p{poly}"
            param_str = f"Window: {window}, Poly: {poly}"
        elif filter_name == "Decimation":
            factor = int(param_widgets['factor_slider'].get())
            new_dir_name = f"{original_dir.name}_{filter_name}_f{factor}"
            param_str = f"Factor: {factor}"
        
        new_dir = original_dir.parent / new_dir_name
        
        # Ask for confirmation
        msg = f"Esto aplicará el filtro {filter_name} a TODAS las {state['total_waveforms']} waveforms.\n\n"
        msg += f"Parámetros: {param_str}\n\n"
        msg += f"Los archivos filtrados se guardarán en:\n{new_dir}\n\n"
        msg += f"¿Continuar?"
        
        if not messagebox.askyesno("Confirmar", msg):
            return
        
        # Create directory
        try:
            new_dir.mkdir(exist_ok=True)
            print(f"\nCreating directory: {new_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el directorio:\n{e}")
            return
        
        # Process all waveforms
        from utils.file_io import read_waveform_file
        
        print(f"\n{'='*60}")
        print(f"Aplicando filtro {filter_name} a {state['total_waveforms']} waveforms...")
        print(f"{'='*60}\n")
        
        success_count = 0
        error_count = 0
        
        for i, wf_path in enumerate(waveform_data.waveform_files):
            try:
                # Read original waveform
                t_half, amplitudes = read_waveform_file(wf_path)
                
                # Apply filter
                filtered_amps = apply_current_filter(amplitudes)
                
                # Save to new file
                new_file_path = new_dir / wf_path.name
                
                # Write filtered data in same format as original
                with open(new_file_path, 'w') as f:
                    # Write header (t_half)
                    f.write(f"{t_half}\n")
                    # Write filtered amplitudes
                    for amp in filtered_amps:
                        f.write(f"{amp}\n")
                
                success_count += 1
                
                # Progress update every 100 files
                if (i + 1) % 100 == 0:
                    print(f"Procesados: {i + 1}/{state['total_waveforms']}")
                    
            except Exception as e:
                print(f"Error procesando {wf_path.name}: {e}")
                error_count += 1
        
        print(f"\n{'='*60}")
        print(f"Proceso completado!")
        print(f"  Exitosos: {success_count}")
        print(f"  Errores: {error_count}")
        print(f"{'='*60}\n")
        
        # Show completion message
        completion_msg = f"✓ Filtrado completado!\n\n"
        completion_msg += f"Archivos procesados: {success_count}/{state['total_waveforms']}\n"
        completion_msg += f"Directorio: {new_dir}\n\n"
        completion_msg += f"IMPORTANTE:\n"
        completion_msg += f"Para usar los datos filtrados, actualiza config.py:\n\n"
        completion_msg += f'DATA_DIR = Path(__file__).parent / "{new_dir_name}"\n\n'
        completion_msg += f"Luego reinicia la aplicación."
        
        messagebox.showinfo("Completado", completion_msg)
    
    apply_all_btn = ctk.CTkButton(
        controls_frame,
        text="Aplicar a Todas",
        command=apply_to_all,
        width=160,
        height=35,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color="#e67e22",
        hover_color="#d35400"
    )
    apply_all_btn.pack(pady=(0, 15))
    
    # Initial plot
    update_plots()
