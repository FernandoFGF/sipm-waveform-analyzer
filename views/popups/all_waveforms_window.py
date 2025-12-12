"""
All waveforms visualization window with filters and sampling.
"""
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue

from config import WINDOW_TIME, SAMPLE_TIME, COLOR_WAVEFORM_OVERLAY
from utils.plotting import save_figure
from views.popups.base_popup import BasePopup

def show_all_waveforms(parent, controller):
    """
    Show all waveforms with filters and sampling controls.
    
    Args:
        parent: Parent window
        controller: Analysis controller with results
    """
    # Create window
    window = BasePopup(parent, "Waveform Completa", 1200, 800)
    
    # Configure grid
    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(0, weight=0)  # Controls
    window.grid_rowconfigure(1, weight=1)  # Plot area
    
    # Controls frame
    controls_frame = ctk.CTkFrame(window, fg_color="transparent")
    controls_frame.grid(row=0, column=0, pady=10, sticky="ew")
    
    # Plot container
    plot_container = ctk.CTkFrame(window)
    plot_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    plot_container.grid_columnconfigure(0, weight=1)
    plot_container.grid_rowconfigure(0, weight=1)
    
    # State variables
    show_accepted = ctk.BooleanVar(value=True)
    show_rejected = ctk.BooleanVar(value=True)
    wf_percentage = 0.1  # Default 10%
    view_mode = 'overlay'  # 'overlay' or 'distributed'
    canvas_refs = {'overlay': None, 'distributed': None}
    
    def get_all_waveforms():
        """Get all waveforms from compatible categories based on filters."""
        waveforms = []
        
        # Accepted (includes normal Accepted + Afterpulses)
        if show_accepted.get():
            waveforms.extend(controller.results.accepted_results)
            waveforms.extend(controller.results.afterpulse_results)
            
        # Rejected
        if show_rejected.get():
            waveforms.extend(controller.results.rejected_results)
            
        return waveforms
    
    def get_plot_style(num_files):
        """Determine alpha and linewidth based on file count."""
        if num_files < 50: return 0.3, 1.5
        elif num_files < 200: return 0.15, 1.3
        elif num_files < 500: return 0.08, 1.1
        else: return 0.04, 1.0
    
    def update_view():
        """Update view based on current mode."""
        nonlocal canvas_refs
        
        # Clear existing canvases
        canvas_refs = {'overlay': None, 'distributed': None}
        
        # Clear container
        for widget in plot_container.winfo_children():
            widget.destroy()
        
        if view_mode == 'overlay':
            create_overlay_view()
        else:
            create_distributed_view()
    
    def show_overlay():
        """Show overlay view."""
        nonlocal view_mode
        view_mode = 'overlay'
        update_view()
    
    def show_distributed():
        """Show distributed view."""
        nonlocal view_mode
        view_mode = 'distributed'
        update_view()
    
    def create_overlay_view():
        """Create overlay plot (local time)."""
        nonlocal canvas_refs
        
        # Show loading message
        loading_label = ctk.CTkLabel(
            plot_container,
            text="Cargando waveforms...",
            font=ctk.CTkFont(size=14)
        )
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Queue for thread communication
        load_queue = queue.Queue()
        
        def load_thread():
            """Background thread to create plot."""
            try:
                all_results = get_all_waveforms()
                total_available = len(all_results)
                
                if total_available == 0:
                    load_queue.put(("empty", None))
                    return
                
                # Apply sampling
                limit = int(total_available * wf_percentage)
                limit = max(1, limit) if total_available > 0 else 0
                
                sampled_results = all_results[:limit]
                alpha, linewidth = get_plot_style(limit)
                
                # Create plot
                fig = plt.Figure(figsize=(12, 8), dpi=100)
                ax = fig.add_subplot(111)
                fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.08)
                
                # Plot waveforms
                for result in sampled_results:
                    t_axis = (np.arange(len(result.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
                    ax.plot(t_axis, result.amplitudes * 1000, 
                           color=COLOR_WAVEFORM_OVERLAY, 
                           linewidth=linewidth, 
                           alpha=alpha)
                
                ax.set_xlabel('Tiempo (µs)', fontsize=10)
                ax.set_ylabel('Amplitud (mV)', fontsize=10)
                ax.set_title(f'Superposición - Tiempo Local ({limit}/{total_available} waveforms)', 
                           fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                load_queue.put(("complete", fig))
                
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                load_queue.put(("error", error_msg))
        
        def check_queue():
            """Check queue for results from background thread."""
            nonlocal canvas_refs
            
            try:
                msg_type, data = load_queue.get_nowait()
                
                if msg_type == "complete":
                    fig = data
                    
                    # Remove loading label
                    loading_label.destroy()
                    
                    # Create canvas
                    canvas = FigureCanvasTkAgg(fig, master=plot_container)
                    canvas.draw()
                    canvas_widget = canvas.get_tk_widget()
                    canvas_widget.pack(fill="both", expand=True)
                    
                    # Add toolbar
                    toolbar_frame = tk.Frame(plot_container)
                    toolbar_frame.pack(side="bottom", fill="x")
                    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                    toolbar.update()
                    
                    canvas_refs['overlay'] = canvas
                
                elif msg_type == "empty":
                    loading_label.configure(
                        text="No hay waveforms seleccionadas.\nActiva al menos un filtro (Aceptados o Rechazados)."
                    )
                
                elif msg_type == "error":
                    loading_label.configure(text=f"Error cargando waveforms:\n{data}")
            
            except queue.Empty:
                window.after(100, check_queue)
        
        # Start background thread
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
        check_queue()
    
    def create_distributed_view():
        """Create distributed plot (global time)."""
        nonlocal canvas_refs
        
        # Show loading message
        loading_label = ctk.CTkLabel(
            plot_container,
            text="Cargando waveforms...",
            font=ctk.CTkFont(size=14)
        )
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Queue for thread communication
        load_queue = queue.Queue()
        
        def load_thread():
            """Background thread to create plot."""
            try:
                all_results = get_all_waveforms()
                total_available = len(all_results)
                
                if total_available == 0:
                    load_queue.put(("empty", None))
                    return
                
                # Apply sampling
                limit = int(total_available * wf_percentage)
                limit = max(1, limit) if total_available > 0 else 0
                
                sampled_results = all_results[:limit]
                alpha, linewidth = get_plot_style(limit)
                
                # Create plot
                fig = plt.Figure(figsize=(14, 8), dpi=100)
                ax = fig.add_subplot(111)
                fig.subplots_adjust(left=0.06, right=0.98, top=0.95, bottom=0.08)
                
                # Plot waveforms with global time
                for result in sampled_results:
                    t_half = result.t_half
                    t_start = t_half - (WINDOW_TIME / 2)
                    t_global = t_start + (np.arange(len(result.amplitudes)) * SAMPLE_TIME)
                    ax.plot(t_global * 1e6, result.amplitudes * 1000, 
                           color=COLOR_WAVEFORM_OVERLAY, 
                           linewidth=linewidth, 
                           alpha=alpha)
                
                ax.set_xlabel('Tiempo Global (µs)', fontsize=10)
                ax.set_ylabel('Amplitud (mV)', fontsize=10)
                ax.set_title(f'Distribuido - Tiempo Global ({limit}/{total_available} waveforms)', 
                           fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                load_queue.put(("complete", fig))
                
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                load_queue.put(("error", error_msg))
        
        def check_queue():
            """Check queue for results from background thread."""
            nonlocal canvas_refs
            
            try:
                msg_type, data = load_queue.get_nowait()
                
                if msg_type == "complete":
                    fig = data
                    
                    # Remove loading label
                    loading_label.destroy()
                    
                    # Create canvas
                    canvas = FigureCanvasTkAgg(fig, master=plot_container)
                    canvas.draw()
                    canvas_widget = canvas.get_tk_widget()
                    canvas_widget.pack(fill="both", expand=True)
                    
                    # Add toolbar
                    toolbar_frame = tk.Frame(plot_container)
                    toolbar_frame.pack(side="bottom", fill="x")
                    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                    toolbar.update()
                    
                    canvas_refs['distributed'] = canvas
                
                elif msg_type == "empty":
                    loading_label.configure(
                        text="No hay waveforms seleccionadas.\nActiva al menos un filtro (Aceptados o Rechazados)."
                    )
                
                elif msg_type == "error":
                    loading_label.configure(text=f"Error cargando waveforms:\n{data}")
            
            except queue.Empty:
                window.after(100, check_queue)
        
        # Start background thread
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
        check_queue()
    
    def on_filter_change():
        """Handle filter checkbox changes."""
        update_view()
    
    def on_percentage_change(value):
        """Handle percentage dropdown change."""
        nonlocal wf_percentage
        # Remove '%' symbol and convert to decimal
        wf_percentage = float(value.rstrip('%')) / 100.0
        update_view()
    
    # Build controls
    # Left: View mode toggle
    view_toggle = ctk.CTkSegmentedButton(
        controls_frame,
        values=["Superposición", "Distribuido"],
        command=lambda v: show_overlay() if v == "Superposición" else show_distributed()
    )
    view_toggle.set("Superposición")
    view_toggle.pack(side="left", padx=10)
    
    # Spacer
    ctk.CTkLabel(controls_frame, text="   |   ", font=ctk.CTkFont(size=14)).pack(side="left")
    
    # Middle: Filters
    ctk.CTkCheckBox(controls_frame, text="Aceptados", variable=show_accepted, 
                   command=on_filter_change, width=80).pack(side="left", padx=5)
    ctk.CTkCheckBox(controls_frame, text="Rechazados", variable=show_rejected,
                   command=on_filter_change, width=80).pack(side="left", padx=5)

    # Spacer
    ctk.CTkLabel(controls_frame, text="   |   ", font=ctk.CTkFont(size=14)).pack(side="left")
    
    # Right: Percentage Dropdown
    dropdown_label = ctk.CTkLabel(controls_frame, text="Muestreo:", font=ctk.CTkFont(size=12, weight="bold"))
    dropdown_label.pack(side="left", padx=(10, 5))
    
    percentage_options = ["1%", "5%", "10%", "25%", "50%", "100%"]
    percentage_dropdown = ctk.CTkOptionMenu(
        controls_frame,
        values=percentage_options,
        command=on_percentage_change,
        width=80
    )
    percentage_dropdown.set("10%")  # Default
    percentage_dropdown.pack(side="left", padx=5)
    
    # Initial plot (overlay mode)
    create_overlay_view()
