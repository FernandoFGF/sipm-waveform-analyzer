"""
Plotting utilities.
"""
import matplotlib.pyplot as plt
from tkinter import filedialog
from datetime import datetime

def save_figure(fig: plt.Figure, default_prefix: str = "plot"):
    """
    Save a matplotlib figure to a file with user dialog.
    
    Args:
        fig: Matplotlib figure to save
        default_prefix: Prefix for the default filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"{default_prefix}_{timestamp}.png"
    
    file_types = [
        ("PNG Image", "*.png"),
        ("PDF Document", "*.pdf"),
        ("SVG Image", "*.svg"),
        ("All Files", "*.*")
    ]
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=file_types,
        initialfile=default_filename,
        title="Guardar Gráfico"
    )
    
    if filepath:
        try:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Gráfico guardado en: {filepath}")
        except Exception as e:
            print(f"Error guardando gráfico: {e}")

def setup_plot_style(ax, title: str = None, xlabel: str = None, ylabel: str = None):
    """
    Apply common style to a plot axes.
    
    Args:
        ax: Matplotlib axes
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
    """
    if title:
        ax.set_title(title, fontsize=12, weight='bold')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
