"""
Peak Finder - SiPM Waveform Analyzer
Main entry point for the application.
"""
import customtkinter as ctk
from config import UI_THEME, UI_COLOR_THEME
from views.main_window import MainWindow


def main():
    """Main application entry point."""
    # Set appearance
    ctk.set_appearance_mode(UI_THEME)
    ctk.set_default_color_theme(UI_COLOR_THEME)
    
    # Create and run application
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
