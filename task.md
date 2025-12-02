# Task: Advanced Analysis Features Implementation

## Phase 1: UI Reorganization
- [ ] Create 2x4 grid layout (2 columns x 4 rows) for all buttons
- [ ] Add "Guardar conf" button to save configuration
- [ ] Update control_sidebar.py layout

## Phase 2: Advanced SiPM Analysis Window
- [ ] Create `advanced_sipm_analysis_window.py`
- [ ] Implement Recovery Time analysis with exponential fit
- [ ] Implement Jitter Temporal analysis
- [ ] Implement Pulse Shape Analysis (rise time, fall time, area, PCA)
- [ ] Create interactive plots for each analysis

## Phase 3: Signal Processing Window
- [ ] Create `signal_processing_window.py`
- [ ] Implement Savitzky-Golay filter
- [ ] Implement Matched filter
- [ ] Implement Wiener filter
- [ ] Implement Wavelet denoising
- [ ] Add before/after comparison view
- [ ] Add navigation (previous/next waveform)
- [ ] Implement "Apply" button to save filtered data

## Phase 4: Filtered Data Management
- [ ] Create utility to save filtered waveforms to new directory
- [ ] Implement naming convention: `{original_dir}-{filter_name}`
- [ ] Update config.py to support filtered data directories
- [ ] Add file I/O for filtered waveforms

## Phase 5: Integration and Testing
- [ ] Connect new windows to sidebar buttons
- [ ] Test signal processing window
- [ ] Test all filters with real data
- [ ] Test data saving and loading
- [ ] Update main window to use filtered data when selected
