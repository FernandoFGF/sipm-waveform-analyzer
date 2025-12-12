"""
Threading mixin for popup windows to prevent UI freezing.
"""
import threading
import queue
import customtkinter as ctk


class ThreadedPopupMixin:
    """Mixin to add threading capabilities to popup windows."""
    
    def setup_threading(self, loading_message="Cargando datos..."):
        """
        Setup threading infrastructure for the popup window.
        
        Args:
            loading_message: Message to show while loading
        """
        self.loading_queue = queue.Queue()
        self.loading_complete = False
        
        # Show loading message
        self.loading_label = ctk.CTkLabel(
            self,
            text=loading_message,
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Start queue checker
        self._check_loading_queue()
    
    def _check_loading_queue(self):
        """Check queue for messages from loading thread (runs every 100ms)."""
        try:
            while True:
                msg_type, data = self.loading_queue.get_nowait()
                
                if msg_type == "complete":
                    # Loading finished successfully
                    if hasattr(self, 'loading_label'):
                        self.loading_label.destroy()
                    self.loading_complete = True
                    # Call completion callback if defined
                    if hasattr(self, '_on_loading_complete'):
                        self._on_loading_complete()
                
                elif msg_type == "error":
                    # Error during loading
                    if hasattr(self, 'loading_label'):
                        self.loading_label.configure(
                            text=f"Error cargando datos:\n{data}"
                        )
        
        except queue.Empty:
            pass
        
        # Schedule next check in 100ms
        if not self.loading_complete:
            self.after(100, self._check_loading_queue)
    
    def run_in_thread(self, target_func, *args, **kwargs):
        """
        Run a function in a background thread.
        
        Args:
            target_func: Function to run in background
            *args, **kwargs: Arguments to pass to the function
        """
        def worker():
            try:
                target_func(*args, **kwargs)
                self.loading_queue.put(("complete", None))
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                self.loading_queue.put(("error", error_msg))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
