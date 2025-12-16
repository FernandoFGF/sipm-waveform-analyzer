"""
Base popup functionality and common dialogs.
"""
import customtkinter as ctk
from tkinter import messagebox

def show_error_dialog(message: str):
    """
    Show error dialog to the user.
    
    Args:
        message: Error message to display
    """
    messagebox.showerror("Error", message)

class BasePopup(ctk.CTkToplevel):
    """Base class for popup windows."""
    
    def __init__(self, parent, title: str, width: int, height: int, scrollable=False):
        """
        Initialize base popup.
        
        Args:
            parent: Parent window
            title: Window title
            width: Window width
            height: Window height
            scrollable: If True, creates a scrollable content frame
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Ensure window stays on top initially
        self.after(100, lambda: self.lift())
        self.after(100, lambda: self.focus_force())
        
        # Create scrollable frame if requested
        if scrollable:
            self.content_frame = ctk.CTkScrollableFrame(
                self,
                orientation="both"  # Both horizontal and vertical scrolling
            )
            self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            self.content_frame = None
