"""
Tabbed comparison window for comparing two datasets across multiple aspects.
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pathlib import Path
import threading
import queue


class TabbedComparisonWindow(ctk.CTkToplevel):
    """Window with tabs for different comparison aspects."""
    
    def __init__(self, parent, controller1, data_dir1, controller2, data_dir2, selected_options):
        """Initialize tabbed comparison window."""
        super().__init__(parent)
        
        self.title(f"Comparación: {data_dir1.name} vs {data_dir2.name}")
        self.geometry("1600x1000")
        
        # Store data
        self.controller1 = controller1
        self.data_dir1 = data_dir1
        self.controller2 = controller2
        self.data_dir2 = data_dir2
        self.selected_options = selected_options
        
        # Navigation state for waveform tabs
        self.waveform_indices = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Threading infrastructure
        self.loading_queue = queue.Queue()
        self.tabs_created = False
        self._start_queue_checker()
        
        # Show loading message
        self.loading_label = ctk.CTkLabel(
            self.tabview,
            text="Cargando comparación...\nEsto puede tardar unos momentos.",
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create tabs in background
        thread = threading.Thread(
            target=self._create_tabs_thread,
            daemon=True
        )
        thread.start()
        
        self.focus()
    
    def _start_queue_checker(self):
        """Start periodic queue checking for tab creation."""
        self._check_loading_queue()
    
    def _check_loading_queue(self):
        """Check queue for messages from loading thread (runs every 100ms)."""
        try:
            while True:
                msg_type, data = self.loading_queue.get_nowait()
                
                if msg_type == "complete":
                    # Tabs created successfully
                    self.loading_label.destroy()
                    self.tabs_created = True
                
                elif msg_type == "error":
                    # Error creating tabs
                    self.loading_label.configure(
                        text=f"Error cargando comparación:\n{data}"
                    )
        
        except queue.Empty:
            pass
        
        # Schedule next check in 100ms
        if not self.tabs_created:
            self.after(100, self._check_loading_queue)
    
    def _create_tabs_thread(self):
        """Background thread worker for tab creation."""
        try:
            self._create_tabs()
            self.loading_queue.put(("complete", None))
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.loading_queue.put(("error", error_msg))
    
    def _create_tabs(self):
        """Create tabs for each selected option."""
        # Map option IDs to tab creation methods
        tab_creators = {
            "visualization": self._create_visualization_tab,
            "amplitude_distribution": self._create_amplitude_distribution_tab,
            "temporal_distribution": self._create_temporal_distribution_tab,
            "charge_histogram": self._create_charge_histogram_tab,
            "all_waveforms": self._create_all_waveforms_tab,
        }
        
        # Create tabs in order
        for option_id in self.selected_options:
            if option_id in tab_creators:
                tab_creators[option_id]()
    
    def _create_visualization_tab(self):
        """Create visualization tab with subtabs for each category."""
        tab = self.tabview.add("Visualización")
        
        # Create sub-tabview
        subtabview = ctk.CTkTabview(tab)
        subtabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create subtabs for each category
        categories = [
            ("Aceptados", "accepted"),
            ("Rechazados", "rejected"),
            ("Afterpulses", "afterpulse"),
            ("Favoritos", "favorites")
        ]
        
        for cat_name, cat_id in categories:
            self._create_waveform_subtab(subtabview, cat_name, cat_id)
    
    def _create_waveform_subtab(self, parent_tabview, tab_name, category):
        """Create a waveform comparison subtab."""
        subtab = parent_tabview.add(tab_name)
        
        # Initialize navigation index
        self.waveform_indices[category] = {'ds1': 0, 'ds2': 0}
        
        # Configure grid
        subtab.grid_columnconfigure(0, weight=1)
        subtab.grid_columnconfigure(1, weight=1)
        subtab.grid_rowconfigure(0, weight=1)
        subtab.grid_rowconfigure(1, weight=0)
        
        # Create plots
        fig1 = plt.Figure(figsize=(7, 6), dpi=100)
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
        
        canvas1 = FigureCanvasTkAgg(fig1, master=subtab)
        canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        fig2 = plt.Figure(figsize=(7, 6), dpi=100)
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
        
        canvas2 = FigureCanvasTkAgg(fig2, master=subtab)
        canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Navigation controls
        nav_frame = ctk.CTkFrame(subtab, fg_color="transparent")
        nav_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")
        
        ctk.CTkButton(nav_frame, text="← Anterior", command=lambda: self._navigate_waveform(category, -1, ax1, ax2, canvas1, canvas2, info_label), width=100).pack(side="left", padx=5)
        ctk.CTkButton(nav_frame, text="Siguiente →", command=lambda: self._navigate_waveform(category, 1, ax1, ax2, canvas1, canvas2, info_label), width=100).pack(side="left", padx=5)
        
        info_label = ctk.CTkLabel(nav_frame, text="", font=ctk.CTkFont(size=11))
        info_label.pack(side="left", padx=20)
        
        # Initial plot
        self._plot_waveforms(category, ax1, ax2, canvas1, canvas2, info_label)
    
    def _navigate_waveform(self, category, direction, ax1, ax2, canvas1, canvas2, info_label):
        """Navigate through waveforms."""
        results1 = self.controller1.get_results_for_category(category)
        results2 = self.controller2.get_results_for_category(category)
        
        if results1:
            new_idx = self.waveform_indices[category]['ds1'] + direction
            if 0 <= new_idx < len(results1):
                self.waveform_indices[category]['ds1'] = new_idx
        
        if results2:
            new_idx = self.waveform_indices[category]['ds2'] + direction
            if 0 <= new_idx < len(results2):
                self.waveform_indices[category]['ds2'] = new_idx
        
        self._plot_waveforms(category, ax1, ax2, canvas1, canvas2, info_label)
    
    def _plot_waveforms(self, category, ax1, ax2, canvas1, canvas2, info_label):
        """Plot waveforms for comparison."""
        from config import WINDOW_TIME, SAMPLE_TIME
        
        ax1.clear()
        ax2.clear()
        
        # Plot dataset 1
        results1 = self.controller1.get_results_for_category(category)
        if results1:
            idx1 = self.waveform_indices[category]['ds1']
            result1 = results1[idx1]
            t_axis = (np.arange(len(result1.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
            
            ax1.plot(t_axis, result1.amplitudes * 1000, color='#3498db', linewidth=1)
            peak_indices = result1.peaks.astype(int) if hasattr(result1.peaks, 'astype') else np.array(result1.peaks, dtype=int)
            ax1.plot(t_axis[peak_indices], result1.amplitudes[peak_indices] * 1000, 
                    'o', color='white', markeredgecolor='black', markersize=6)
            
            ax1.set_title(f"DS1: {result1.filename} ({len(result1.peaks)} picos)", fontsize=10)
            ax1.set_xlabel("Tiempo (µs)", fontsize=9)
            ax1.set_ylabel("Amplitud (mV)", fontsize=9)
            ax1.grid(True, alpha=0.3)
        
        # Plot dataset 2
        results2 = self.controller2.get_results_for_category(category)
        if results2:
            idx2 = self.waveform_indices[category]['ds2']
            result2 = results2[idx2]
            t_axis = (np.arange(len(result2.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
            
            ax2.plot(t_axis, result2.amplitudes * 1000, color='#e74c3c', linewidth=1)
            peak_indices = result2.peaks.astype(int) if hasattr(result2.peaks, 'astype') else np.array(result2.peaks, dtype=int)
            ax2.plot(t_axis[peak_indices], result2.amplitudes[peak_indices] * 1000,
                    'o', color='white', markeredgecolor='black', markersize=6)
            
            ax2.set_title(f"DS2: {result2.filename} ({len(result2.peaks)} picos)", fontsize=10)
            ax2.set_xlabel("Tiempo (µs)", fontsize=9)
            ax2.set_ylabel("Amplitud (mV)", fontsize=9)
            ax2.grid(True, alpha=0.3)
        
        canvas1.draw()
        canvas2.draw()
        
        # Update info
        info_text = ""
        if results1:
            info_text = f"DS1: {self.waveform_indices[category]['ds1'] + 1}/{len(results1)}"
        if results2:
            if info_text:
                info_text += "  |  "
            info_text += f"DS2: {self.waveform_indices[category]['ds2'] + 1}/{len(results2)}"
        info_label.configure(text=info_text)
    
    def _create_amplitude_distribution_tab(self):
        """Create amplitude distribution comparison tab."""
        tab = self.tabview.add("Amplitudes")
        
        # Create comparison plot
        fig = plt.Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.1)
        
        # Collect amplitude data if not already available
        def get_all_amplitudes(controller):
            """Get all amplitudes, collecting from results if needed."""
            if hasattr(controller.waveform_data, 'all_amplitudes_flat') and \
               controller.waveform_data.all_amplitudes_flat is not None and \
               controller.waveform_data.all_amplitudes_flat.size > 0:
                return controller.waveform_data.all_amplitudes_flat
            
            # Fallback: collect from results
            all_amps = []
            for result in controller.results.accepted_results:
                all_amps.extend(result.amplitudes)
            for result in controller.results.afterpulse_results:
                all_amps.extend(result.amplitudes)
            for result in controller.results.rejected_results:
                all_amps.extend(result.amplitudes)
            
            return np.array(all_amps) if all_amps else np.array([])
        
        # Plot both distributions
        amps1 = get_all_amplitudes(self.controller1)
        amps2 = get_all_amplitudes(self.controller2)
        
        if amps1.size > 0:
            ax.hist(amps1 * 1000, bins=50, alpha=0.6, 
                   label=self.data_dir1.name, color='#3498db')
        
        if amps2.size > 0:
            ax.hist(amps2 * 1000, bins=50, alpha=0.6, 
                   label=self.data_dir2.name, color='#e74c3c')
        
        ax.set_xlabel('Amplitud (mV)')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Comparación de Distribución de Amplitudes')
        
        # Only show legend if we have data
        if amps1.size > 0 or amps2.size > 0:
            ax.legend()
        
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
    
    def _create_temporal_distribution_tab(self):
        """Create temporal distribution + FFT comparison tab."""
        tab = self.tabview.add("Temporal")
        
        # Create grid layout for side-by-side plots
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        from config import WINDOW_TIME, SAMPLE_TIME
        
        def get_temporal_data(controller):
            """Get temporal distribution data (diffs vs amplitudes)."""
            all_global_peaks = []
            all_results = controller.results.accepted_results + controller.results.afterpulse_results
            
            for res in all_results:
                t_half = res.t_half
                peaks_indices = res.peaks
                amplitudes = res.amplitudes
                t_start_window = t_half - (WINDOW_TIME / 2)
                
                for p_idx in peaks_indices:
                    t_rel = p_idx * SAMPLE_TIME
                    t_global = t_start_window + t_rel
                    amp = amplitudes[p_idx]
                    all_global_peaks.append((t_global, amp))
            
            if len(all_global_peaks) < 2:
                return np.array([]), np.array([]), None
            
            all_global_peaks.sort(key=lambda x: x[0])
            times = np.array([p[0] for p in all_global_peaks])
            amps = np.array([p[1] for p in all_global_peaks])
            
            diffs = np.diff(times)
            amps_plot = amps[1:] * 1000  # Convert to mV
            
            # Get first accepted result for FFT
            first_result = controller.results.accepted_results[0] if controller.results.accepted_results else None
            return diffs, amps_plot, first_result
        
        diffs1, amps1, result1 = get_temporal_data(self.controller1)
        diffs2, amps2, result2 = get_temporal_data(self.controller2)
        
        # Left: Temporal distribution (overlaid)
        fig1 = plt.Figure(figsize=(7, 6), dpi=100)
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
        
        if len(diffs1) > 0:
            ax1.scatter(diffs1, amps1, alpha=0.4, s=8, c='#3498db', label=self.data_dir1.name, edgecolors='none')
        
        if len(diffs2) > 0:
            ax1.scatter(diffs2, amps2, alpha=0.4, s=8, c='#e74c3c', label=self.data_dir2.name, edgecolors='none')
        
        ax1.set_xscale('log')
        ax1.set_xlabel('Diferencia Temporal (s) [Log]')
        ax1.set_ylabel('Amplitud (mV)')
        ax1.set_title('Distribución Temporal')
        ax1.legend()
        ax1.grid(True, which="both", ls="-", alpha=0.2)
        
        canvas1 = FigureCanvasTkAgg(fig1, master=tab)
        canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        canvas1.draw()
        
        # Right: FFT comparison
        fig2 = plt.Figure(figsize=(7, 6), dpi=100)
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
        
        if result1:
            fft1 = np.fft.fft(result1.amplitudes)
            freq1 = np.fft.fftfreq(len(result1.amplitudes), SAMPLE_TIME)
            pos_mask1 = freq1 > 0
            ax2.plot(freq1[pos_mask1] / 1e6, np.abs(fft1[pos_mask1]), color='#3498db', linewidth=1, label=self.data_dir1.name, alpha=0.7)
        
        if result2:
            fft2 = np.fft.fft(result2.amplitudes)
            freq2 = np.fft.fftfreq(len(result2.amplitudes), SAMPLE_TIME)
            pos_mask2 = freq2 > 0
            ax2.plot(freq2[pos_mask2] / 1e6, np.abs(fft2[pos_mask2]), color='#e74c3c', linewidth=1, label=self.data_dir2.name, alpha=0.7)
        
        ax2.set_xlabel('Frecuencia (MHz)')
        ax2.set_ylabel('Magnitud')
        ax2.set_title('Espectro de Frecuencias (FFT)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        
        canvas2 = FigureCanvasTkAgg(fig2, master=tab)
        canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        canvas2.draw()
    
    def _create_charge_histogram_tab(self):
        """Create charge histogram comparison tab."""
        tab = self.tabview.add("Carga")
        
        # Create single comparison plot
        fig = plt.Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.1)
        
        from config import SAMPLE_TIME
        
        # Calculate charges for dataset 1 (integral = V * s)
        charges1 = []
        for result in self.controller1.results.accepted_results:
            if len(result.peaks) > 0:
                peak_indices = result.peaks.astype(int) if hasattr(result.peaks, 'astype') else np.array(result.peaks, dtype=int)
                # Charge = amplitude * time_per_sample
                peak_charges = result.amplitudes[peak_indices] * SAMPLE_TIME
                charges1.extend(peak_charges)
        
        # Calculate charges for dataset 2
        charges2 = []
        for result in self.controller2.results.accepted_results:
            if len(result.peaks) > 0:
                peak_indices = result.peaks.astype(int) if hasattr(result.peaks, 'astype') else np.array(result.peaks, dtype=int)
                peak_charges = result.amplitudes[peak_indices] * SAMPLE_TIME
                charges2.extend(peak_charges)
        
        # Plot both histograms
        if charges1:
            ax.hist(charges1, bins=50, alpha=0.6, label=self.data_dir1.name, color='#3498db')
        
        if charges2:
            ax.hist(charges2, bins=50, alpha=0.6, label=self.data_dir2.name, color='#e74c3c')
        
        ax.set_xlabel('Carga (V·s)')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Comparación de Histograma de Carga')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
    
    def _create_all_waveforms_tab(self):
        """Create all waveforms tab with toggle between overlay and distributed."""
        tab = self.tabview.add("Waveform Completa")
        
        # Configure grid
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=0)  # Controls
        tab.grid_rowconfigure(1, weight=1)  # Plot area
        
        # Controls frame (Toggle + Slider)
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.grid(row=0, column=0, pady=10, sticky="ew")
        
        # Plot container
        plot_container = ctk.CTkFrame(tab)
        plot_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        plot_container.grid_columnconfigure(0, weight=1)
        plot_container.grid_columnconfigure(1, weight=1) # Ensure 2 columns available
        plot_container.grid_rowconfigure(0, weight=1)
        
        # State
        self.wf_percentage = 0.1 # Default 10%
        self.view_mode = 'overlay' # 'overlay' or 'distributed'
        self.show_accepted = ctk.BooleanVar(value=True)
        self.show_rejected = ctk.BooleanVar(value=True)
        canvas_refs = {'overlay': None, 'distributed': None}
        
        def get_all_waveforms(controller):
            """Get all waveforms from compatible categories based on filters."""
            waveforms = []
            
            # Accepted (includes normal Accepted + Afterpulses)
            if self.show_accepted.get():
                waveforms.extend(controller.results.accepted_results)
                waveforms.extend(controller.results.afterpulse_results)
                
            # Rejected
            if self.show_rejected.get():
                waveforms.extend(controller.results.rejected_results)
                
            return waveforms

        def get_plot_style(num_files):
            """Determine alpha and linewidth based on file count."""
            if num_files < 50: return 0.3, 1.5
            elif num_files < 200: return 0.15, 1.3
            elif num_files < 500: return 0.08, 1.1
            else: return 0.04, 1.0

        def update_view():
            """Update currently selected view."""
            if self.view_mode == 'overlay':
                show_overlay()
            else:
                show_distributed()

        def on_filter_change():
            """Handle checkbox change."""
            # Force recreation of plots
            canvas_refs['overlay'] = None
            canvas_refs['distributed'] = None
            
            # Clear container
            for widget in plot_container.winfo_children():
                widget.destroy()
            
            update_view()

        def show_overlay():
            """Show overlay view (side-by-side local time)."""
            self.view_mode = 'overlay'
            
            # Hide distributed
            if canvas_refs['distributed']:
                canvas_refs['distributed'].get_tk_widget().grid_remove()
            
            # Show/Create overlay
            if canvas_refs['overlay']:
                for canvas in canvas_refs['overlay']:
                    canvas.get_tk_widget().grid()
            else:
                create_overlay_view()
        
        def show_distributed():
            """Show distributed view (separated plots global time)."""
            self.view_mode = 'distributed'
            
            # Hide overlay
            if canvas_refs['overlay']:
                for canvas in canvas_refs['overlay']:
                    canvas.get_tk_widget().grid_remove()
            
            # Show/Create distributed
            if canvas_refs['distributed']:
                canvas_refs['distributed'].get_tk_widget().grid()
            else:
                create_distributed_view()
        
        def create_overlay_view():
            """Create side-by-side plots (Local Time)."""
            from config import WINDOW_TIME, SAMPLE_TIME
            
            # Ensure two columns for side-by-side
            plot_container.grid_columnconfigure(0, weight=1)
            plot_container.grid_columnconfigure(1, weight=1)
            
            def plot_dataset(ax, controller, name, color):
                all_results = get_all_waveforms(controller)
                total_available = len(all_results)
                
                if total_available == 0:
                    ax.text(0.5, 0.5, "No waveforms selected", ha='center', va='center')
                    ax.set_title(f'{name} (0)')
                    return 0
                
                # Apply sampling based on percentage
                limit = int(total_available * self.wf_percentage)
                limit = max(1, limit) if total_available > 0 else 0
                
                sampled_results = all_results[:limit]
                alpha, linewidth = get_plot_style(limit)
                
                for result in sampled_results:
                    t_axis = (np.arange(len(result.amplitudes)) * SAMPLE_TIME - WINDOW_TIME/2) * 1e6
                    ax.plot(t_axis, result.amplitudes * 1000, color=color, 
                           linewidth=linewidth, alpha=alpha)
                
                ax.set_xlabel('Tiempo (µs)')
                ax.set_ylabel('Amplitud (mV)')
                ax.set_title(f'{name} ({limit}/{total_available} waveforms)')
                ax.grid(True, alpha=0.3)
                return limit

            # Dataset 1
            fig1 = plt.Figure(figsize=(7, 6), dpi=100)
            ax1 = fig1.add_subplot(111)
            fig1.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
            plot_dataset(ax1, self.controller1, f"DS1: {self.data_dir1.name}", '#3498db')
            
            canvas1 = FigureCanvasTkAgg(fig1, master=plot_container)
            canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            canvas1.draw()
            
            # Dataset 2
            fig2 = plt.Figure(figsize=(7, 6), dpi=100)
            ax2 = fig2.add_subplot(111)
            fig2.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.1)
            plot_dataset(ax2, self.controller2, f"DS2: {self.data_dir2.name}", '#e74c3c')
            
            canvas2 = FigureCanvasTkAgg(fig2, master=plot_container)
            canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            canvas2.draw()
            
            canvas_refs['overlay'] = [canvas1, canvas2]
        
        def create_distributed_view():
            """Create top-bottom plots (Global Time)."""
            from config import WINDOW_TIME, SAMPLE_TIME
            
            # Single column for top-down plots
            plot_container.grid_columnconfigure(0, weight=1)
            plot_container.grid_columnconfigure(1, weight=0) # Hide 2nd column
            
            fig = plt.Figure(figsize=(14, 8), dpi=100)
            # Create two subplots vertically
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212, sharex=ax1) # Share x axis
            fig.subplots_adjust(left=0.06, right=0.98, top=0.95, bottom=0.08, hspace=0.3)
            
            # Helper to plot global
            def plot_global(ax, controller, name, color):
                all_results = get_all_waveforms(controller)
                total_available = len(all_results)
                
                if total_available == 0:
                    ax.text(0.5, 0.5, "No waveforms selected", ha='center', va='center')
                    ax.set_title(f'{name} (0)')
                    return

                limit = int(total_available * self.wf_percentage)
                limit = max(1, limit) if total_available > 0 else 0
                
                sampled_results = all_results[:limit]
                alpha, linewidth = get_plot_style(limit)
                
                for result in sampled_results:
                    t_half = result.t_half
                    t_start = t_half - (WINDOW_TIME / 2)
                    t_global = t_start + (np.arange(len(result.amplitudes)) * SAMPLE_TIME)
                    ax.plot(t_global * 1e6, result.amplitudes * 1000, 
                           color=color, linewidth=linewidth, alpha=alpha)
                
                ax.set_ylabel('Amplitud (mV)', fontsize=10)
                ax.set_title(f'{name} - Temporal Global ({limit}/{total_available})', fontsize=11)
                ax.grid(True, alpha=0.3)
                # Explicit legend location to avoid warning
                ax.legend([name], loc='upper right', fontsize=8) 
            
            plot_global(ax1, self.controller1, f"DS1: {self.data_dir1.name}", '#3498db')
            plot_global(ax2, self.controller2, f"DS2: {self.data_dir2.name}", '#e74c3c')
            
            ax2.set_xlabel('Tiempo Global (µs)', fontsize=12)
            
            canvas = FigureCanvasTkAgg(fig, master=plot_container)
            canvas.get_tk_widget().grid(row=0, column=0, columnspan=2, sticky="nsew")
            canvas.draw()
            
            canvas_refs['distributed'] = canvas
        
        # --- UI Controls Layout ---
        
        # Left: Toggle Buttons
        ctk.CTkLabel(controls_frame, text="Modo:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
        
        mode_btn1 = ctk.CTkButton(controls_frame, text="Superposición", command=show_overlay,
                                 width=100, fg_color="#3498db", hover_color="#2980b9")
        mode_btn1.pack(side="left", padx=5)
        
        mode_btn2 = ctk.CTkButton(controls_frame, text="Distribuida", command=show_distributed,
                                 width=100, fg_color="#9b59b6", hover_color="#8e44ad")
        mode_btn2.pack(side="left", padx=5)
        
        # Spacer
        ctk.CTkLabel(controls_frame, text="   |   ", font=ctk.CTkFont(size=14)).pack(side="left")
        
        # Middle: Filters
        ctk.CTkCheckBox(controls_frame, text="Aceptados", variable=self.show_accepted, 
                       command=on_filter_change, width=80).pack(side="left", padx=5)
        ctk.CTkCheckBox(controls_frame, text="Rechazados", variable=self.show_rejected,
                       command=on_filter_change, width=80).pack(side="left", padx=5)

        # Spacer
        ctk.CTkLabel(controls_frame, text="   |   ", font=ctk.CTkFont(size=14)).pack(side="left")
        
        # Right: Percentage Dropdown
        dropdown_label = ctk.CTkLabel(controls_frame, text="Muestreo:", font=ctk.CTkFont(size=12, weight="bold"))
        dropdown_label.pack(side="left", padx=(10, 5))
        
        def on_dropdown_change(value):
            """Handle dropdown change."""
            # Value comes as string "10%", "25%", etc.
            pct_str = value.replace("%", "")
            try:
                target_pct = int(pct_str) / 100.0
            except ValueError:
                target_pct = 0.10
            
            if target_pct != self.wf_percentage:
                self.wf_percentage = target_pct
                
                # Force recreation of plots
                canvas_refs['overlay'] = None
                canvas_refs['distributed'] = None
                
                # Clear container
                for widget in plot_container.winfo_children():
                    widget.destroy()
                
                update_view()

        sampling_values = ["10%", "25%", "50%", "75%", "100%"]
        dropdown = ctk.CTkOptionMenu(
            controls_frame,
            values=sampling_values,
            command=on_dropdown_change,
            width=100
        )
        dropdown.set("10%") # Initial value
        dropdown.pack(side="left", padx=5)
        
        # Initial View
        create_overlay_view()


def show_tabbed_comparison_window(parent, controller1, data_dir1, controller2, data_dir2, selected_options):
    """Show tabbed comparison window."""
    window = TabbedComparisonWindow(parent, controller1, data_dir1, controller2, data_dir2, selected_options)
    window.focus()
