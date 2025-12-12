"""
Signal processing window with filter preview - SIMPLIFIED VERSION
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import SAMPLE_TIME
from models.signal_filters import apply_savitzky_golay, calculate_snr_improvement, calculate_rms_noise
from views.popups.base_popup import BasePopup


def show_signal_processing(parent, waveform_data, current_results):
    """Show signal processing window with filter preview."""
    if not waveform_data or not waveform_data.waveform_files:
        print("No waveform data available")
        return
    
    # Create window
    window = BasePopup(parent, "Procesamiento de Señal - Smoothing", 1200, 600)
    
    # Create main frame with two columns (Controls | Plot)
    main_frame = ctk.CTkFrame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=1, minsize=300)  # Controls
    main_frame.grid_columnconfigure(1, weight=3)  # One big plot
    main_frame.grid_rowconfigure(0, weight=1)
    
    # Left: Controls panel
    controls_frame = ctk.CTkFrame(main_frame)
    controls_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    
    # Right: Plot panel
    plot_frame = ctk.CTkFrame(main_frame)
    plot_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    
    # State variables
    # State variables
    state = {
        'current_idx': 0,
        'total_waveforms': len(waveform_data.waveform_files),
        'canvas': None,
        'fig': None,
        'ax': None,
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
            # Increased range significantly to allow for visible smoothing on clean signals
            window_slider = ctk.CTkSlider(params_frame, from_=5, to=301, number_of_steps=148, command=on_window_change, width=150)
            window_slider.set(51) # Default higher for visibility
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
    
    # Combined View + Navigation Frame
    combined_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    combined_frame.pack(fill="x", padx=5, pady=10)
    combined_frame.grid_columnconfigure(0, weight=1)
    combined_frame.grid_columnconfigure(1, weight=1)
    
    # Left: View Controls
    view_frame = ctk.CTkFrame(combined_frame, fg_color="transparent")
    view_frame.grid(row=0, column=0, sticky="nw", padx=5)
    
    ctk.CTkLabel(view_frame, text="Visualización", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
    
    show_orig_var = ctk.BooleanVar(value=True)
    show_filt_var = ctk.BooleanVar(value=True)
    
    def on_view_change():
        update_plots()
        
    ctk.CTkCheckBox(view_frame, text="Original", variable=show_orig_var, command=on_view_change, font=ctk.CTkFont(size=10), width=60, height=20).pack(anchor="w", pady=2)
    ctk.CTkCheckBox(view_frame, text="Filtrado", variable=show_filt_var, command=on_view_change, font=ctk.CTkFont(size=10), width=60, height=20).pack(anchor="w", pady=2)
    
    # Right: Navigation Controls
    nav_frame = ctk.CTkFrame(combined_frame, fg_color="transparent")
    nav_frame.grid(row=0, column=1, sticky="ne", padx=5)
    
    ctk.CTkLabel(nav_frame, text="Navegación", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="e")
    
    current_label = ctk.CTkLabel(nav_frame, text=f"1 / {state['total_waveforms']}", font=ctk.CTkFont(size=12))
    current_label.pack(pady=2, anchor="e")
    
    nav_buttons_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
    nav_buttons_frame.pack(pady=2, anchor="e")
    
    def navigate_prev():
        if state['current_idx'] > 0:
            state['current_idx'] -= 1
            update_plots()
    
    def navigate_next():
        if state['current_idx'] < state['total_waveforms'] - 1:
            state['current_idx'] += 1
            update_plots()
    
    prev_btn = ctk.CTkButton(nav_buttons_frame, text="◄", command=navigate_prev, width=30, height=25, font=ctk.CTkFont(size=12))
    prev_btn.pack(side="left", padx=2)
    
    next_btn = ctk.CTkButton(nav_buttons_frame, text="►", command=navigate_next, width=30, height=25, font=ctk.CTkFont(size=12))
    next_btn.pack(side="left", padx=2)
    
    # Filename label (below combined)
    filename_label = ctk.CTkLabel(
        controls_frame,
        text="",
        font=ctk.CTkFont(size=9),
        text_color="#7f8c8d",
        wraplength=280
    )
    filename_label.pack(pady=(0, 10))
    
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
        try:
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
        except Exception as e:
            print(f"Error applying filter {filter_name}: {e}")
            return amplitudes.copy()
            
        return amplitudes.copy()
    
    def update_plots():
        """Update the plot with original and filtered signals."""
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
        
        # Create time array for filtered signal
        times_filtered = np.arange(len(filtered_amps)) * SAMPLE_TIME * 1e6
        if state['current_filter'] == "Decimation":
            factor = int(param_widgets['factor_slider'].get())
            times_filtered = np.arange(len(filtered_amps)) * SAMPLE_TIME * factor * 1e6
        
        # Convert to mV
        amps_mv = amplitudes * 1000
        filtered_mv = filtered_amps * 1000
        
        # Update labels
        filename_label.configure(text=wf_path.name)
        current_label.configure(text=f"{idx + 1} / {state['total_waveforms']}")
        
        # Calculate metrics
        try:
            snr_improvement = calculate_snr_improvement(amplitudes, filtered_amps)
            rms_before = calculate_rms_noise(amplitudes) * 1000
            rms_after = calculate_rms_noise(filtered_amps) * 1000
            
            snr_label.configure(text=f"SNR: {snr_improvement:+.2f} dB")
            rms_before_label.configure(text=f"RMS antes: {rms_before:.3f} mV")
            rms_after_label.configure(text=f"RMS después: {rms_after:.3f} mV")
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            snr_label.configure(text="SNR: Error")
            # ...
        
        # --- Plotting ---
        if state['fig'] is None:
            # Create larger figure
            state['fig'] = plt.Figure(figsize=(8, 6), dpi=100)
            state['ax'] = state['fig'].add_subplot(111)
            # Adjust margins
            state['fig'].subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.08)
            
        ax = state['ax']
        ax.clear()
        
        # 1. Plot Original (Gray, thinner, semi-transparent)
        if show_orig_var.get():
            ax.plot(times, amps_mv, linewidth=0.8, color='gray', alpha=0.5, label='Original')
        
        # 2. Plot Filtered (Green/Vibrant, slightly thicker)
        if show_filt_var.get():
            ax.plot(times_filtered, filtered_mv, linewidth=1.5, color='#27ae60', label='Filtrado')
        
        # Setup title with params
        title_text = f"Filtro: {state['current_filter']}"
        if state['current_filter'] == "Smoothing":
             w = int(param_widgets['window_slider'].get())
             p = int(param_widgets['poly_slider'].get())
             title_text += f" (W={w}, P={p})"
        elif state['current_filter'] == "Decimation":
             f = int(param_widgets['factor_slider'].get())
             title_text += f" (Factor={f})"
             
        ax.set_title(title_text, fontsize=12, weight='bold')
        ax.set_xlabel("Tiempo (µs)")
        ax.set_ylabel("Amplitud (mV)")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Canvas management
        if state['canvas'] is None:
            state['canvas'] = FigureCanvasTkAgg(state['fig'], master=plot_frame)
            state['canvas'].get_tk_widget().pack(fill="both", expand=True)
        
        state['canvas'].draw()
        state['canvas'].get_tk_widget().update_idletasks()
        state['canvas'].flush_events()
        
    
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
            
            # Copy DATA.txt if it exists
            import shutil
            data_txt_path = original_dir / "DATA.txt"
            if data_txt_path.exists():
                shutil.copy2(data_txt_path, new_dir / "DATA.txt")
                print("Copied DATA.txt to new directory")
                
                # If Decimation, we MUST update 'Num de puntos(real)' in DATA.txt
                # otherwise the app will load it with the original SAMPLE_TIME and the time axis will be wrong
                if filter_name == "Decimation":
                    try:
                        new_data_txt = new_dir / "DATA.txt"
                        if new_data_txt.exists():
                            with open(new_data_txt, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            
                            # Estimate new number of points (taking the length of the first filtered waveform)
                            # We can just run the filter on the first file to check length
                            # But better: we are inside the loop? No, we are before the loop.
                            # So let's calculate it from the first file.
                            
                            # Read first file to get original length
                            from utils.file_io import read_waveform_file
                            first_wf = waveform_data.waveform_files[0]
                            _, amp_temp = read_waveform_file(first_wf)
                            filtered_temp = apply_current_filter(amp_temp)
                            new_len = len(filtered_temp)
                            
                            updated_lines = []
                            for line in lines:
                                if "Num de puntos(real):" in line:
                                    updated_lines.append(f"Num de puntos(real): {new_len}\n")
                                else:
                                    updated_lines.append(line)
                            
                            with open(new_data_txt, 'w', encoding='utf-8') as f:
                                f.writelines(updated_lines)
                            print(f"Updated DATA.txt with Num de puntos(real): {new_len}")
                            
                    except Exception as e:
                        print(f"Warning: Could not update DATA.txt point count: {e}")

            else:
                print("Warning: DATA.txt not found in source directory")
                
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
                # Extract index from original filename (assuming format Name_Index.txt)
                try:
                    # Get the last part after splitting by '_'
                    original_stem = wf_path.stem
                    # Find the last underscore to isolate the index
                    last_underscore_idx = original_stem.rfind('_')
                    if last_underscore_idx != -1:
                        suffix = original_stem[last_underscore_idx:] # e.g., "_0"
                    else:
                        # Fallback if no underscore found
                        suffix = f"_{i}"
                except:
                    suffix = f"_{i}"

                # New filename: DirectoryName + Suffix + Extension
                new_filename = f"{new_dir_name}{suffix}{wf_path.suffix}"
                new_file_path = new_dir / new_filename
                
                # Write filtered data in same format as original
                with open(new_file_path, 'w') as f:
                    # Write header (t_half)
                    f.write(f"{t_half}\n")
                    f.write("\n") # Restore blank line required by format
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
