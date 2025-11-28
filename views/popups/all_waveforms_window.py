"""
All waveforms visualization window.
"""
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

from config import WINDOW_TIME, SAMPLE_TIME, COLOR_WAVEFORM_OVERLAY
from utils.plotting import save_figure
from views.popups.base_popup import BasePopup

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
    window = BasePopup(parent, "Todas las Waveforms", 1200, 800)
    
    # Create frame for plot and toolbar
    plot_frame = ctk.CTkFrame(window)
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
    
    # Setup context menu
    context_menu = tk.Menu(window, tearoff=0)
    
    def save_plot(fmt):
        save_figure(fig, default_prefix="all_waveforms")

    context_menu.add_command(label="💾 Guardar como PNG", command=lambda: save_plot("png"))
    context_menu.add_command(label="💾 Guardar como PDF", command=lambda: save_plot("pdf"))
    context_menu.add_command(label="💾 Guardar como SVG", command=lambda: save_plot("svg"))
    
    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    canvas.get_tk_widget().bind("<Button-3>", show_context_menu)
    
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
        window,
        text="💡 Usa la barra de herramientas: 🏠 Reset | ← → Navegar | 🔍 Zoom (selecciona área) | ✋ Pan (arrastra) | 🖱️ Click derecho para alejar",
        font=ctk.CTkFont(size=10)
    )
    info_label.pack(side="bottom", pady=(0, 5))
