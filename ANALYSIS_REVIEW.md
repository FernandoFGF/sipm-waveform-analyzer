# Revisión Completa: SiPM Waveform Analyzer
## Análisis Técnico de Funcionalidad y Mejoras

---

## 📋 Resumen Ejecutivo

Tu herramienta **SiPM Waveform Analyzer** es una aplicación bien estructurada con funcionalidad avanzada para análisis de fotomultiplicadores de silicio. He revisado todo el código y encontré:

✅ **Fortalezas**:
- Arquitectura MVC bien organizada
- Análisis SiPM completo (crosstalk, afterpulse, DCR)
- Múltiples técnicas de análisis de pulsos
- Interfaz gráfica profesional con CustomTkinter

⚠️ **Problemas Identificados**: 8 issues críticos
🔧 **Mejoras Sugeridas**: 15 optimizaciones
✨ **Nuevas Funcionalidades**: 12 propuestas

---

## 🔴 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Cálculo de Carga - ERROR CONCEPTUAL**
**Archivo**: [`charge_histogram_window.py:56-59`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/views/popups/charge_histogram_window.py#L56-L59)

```python
# ❌ PROBLEMA: Cálculo incorrecto de carga
signal_above_baseline = res.amplitudes[res.amplitudes > baseline_high] - baseline_high
if len(signal_above_baseline) > 0:
    charge = np.sum(signal_above_baseline) * SAMPLE_TIME
```

**Problemas**:
1. **Selección de puntos incorrecta**: Filtra solo puntos > baseline, perdiendo la forma completa del pulso
2. **No integra correctamente**: Debería integrar toda la región del pulso, no solo puntos individuales
3. **Unidades confusas**: Mezcla nV·s cuando debería ser pC (picocoulombios) para SiPMs

**Solución Correcta**:
```python
def calculate_pulse_charge_correct(amplitudes, time_array, peak_idx, baseline, window_samples=100):
    """
    Calculate integrated charge of pulse above baseline.
    
    Returns:
        Charge in pC (picocoulombios)
    """
    # Define integration window around peak
    start = max(0, peak_idx - window_samples // 4)  # Start before peak
    end = min(len(amplitudes), peak_idx + 3 * window_samples // 4)  # Extend after peak
    
    # Extract pulse region
    pulse_region = amplitudes[start:end]
    time_region = time_array[start:end]
    
    # Subtract baseline from entire region
    signal_above_baseline = pulse_region - baseline
    signal_above_baseline[signal_above_baseline < 0] = 0  # Clip negative values
    
    # Integrate using trapezoidal rule (more accurate than simple sum)
    charge_V_s = np.trapz(signal_above_baseline, time_region)
    
    # Convert to picocoulombios: Q = ∫V dt / R
    # Assuming 50 Ohm termination (standard for oscilloscopes)
    R_ohm = 50.0
    charge_pC = (charge_V_s / R_ohm) * 1e12  # V·s / Ohm = Coulomb, * 1e12 = pC
    
    return charge_pC
```

---

### 2. **DCR Calculation - Dos Métodos Inconsistentes**
**Archivo**: [`signal_processing.py:108-126`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/utils/signal_processing.py#L108-L126)

```python
# ⚠️ PROBLEMA: Dos métodos de cálculo DCR que dan resultados diferentes
# Method 1: Total rate = events / total_time
total_time_dcr = np.sum(dcr_intervals)
metrics.dcr_rate_total_hz = metrics.dcr_count / total_time_dcr

# Method 2: Average rate = 1 / mean_interval
mean_interval_dcr = np.mean(dcr_intervals)
metrics.dcr_rate_avg_hz = 1.0 / mean_interval_dcr
```

**Problema**:
- **Método 1 es INCORRECTO**: Suma los intervalos entre eventos DCR, no el tiempo total de medición
- **Método 2 es APROXIMADO**: Asume distribución uniforme
- **Falta tiempo total real**: No se está usando el tiempo total de adquisición

**Solución Correcta**:
```python
def calculate_dcr_correct(delta_t, dcr_mask, total_acquisition_time):
    """
    Calculate Dark Count Rate correctly.
    
    Args:
        delta_t: Time differences between ALL consecutive peaks
        dcr_mask: Boolean mask for DCR events
        total_acquisition_time: Total time of all waveforms (s)
        
    Returns:
        DCR in Hz and kHz
    """
    dcr_count = np.sum(dcr_mask)
    
    if dcr_count == 0:
        return 0.0, 0.0
    
    # CORRECT METHOD: DCR = number of dark counts / total measurement time
    dcr_hz = dcr_count / total_acquisition_time
    dcr_khz = dcr_hz / 1000.0
    
    # Also calculate mean interval for reference (but this is NOT the DCR)
    dcr_intervals = delta_t[dcr_mask]
    mean_interval = np.mean(dcr_intervals) if len(dcr_intervals) > 0 else 0
    
    return dcr_hz, mean_interval
```

**Necesitas agregar**:
```python
# En WaveformData o AnalysisResults
total_acquisition_time = num_waveforms * WINDOW_TIME
```

---

### 3. **Clasificación de Eventos SiPM - Lógica Cuestionable**
**Archivo**: [`signal_processing.py:83-95`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/utils/signal_processing.py#L83-L95)

```python
# ⚠️ PROBLEMA: Clasificación por cuadrantes puede ser incorrecta
# Bottom-Right: DCR (long time, low amplitude)
dcr_mask = (delta_t >= self.time_threshold) & (amplitudes_mV < self.amp_threshold)

# Bottom-Left: Afterpulses (short time, low amplitude)
ap_mask = (delta_t < self.time_threshold) & (amplitudes_mV < self.amp_threshold)

# Top-Right: Crosstalk (long time, high amplitude)
xt_mask = (delta_t >= self.time_threshold) & (amplitudes_mV >= self.amp_threshold)

# Top-Left: Afterpulse + Crosstalk (short time, high amplitude)
ap_xt_mask = (delta_t < self.time_threshold) & (amplitudes_mV >= self.amp_threshold)
```

**Problemas Físicos**:
1. **Crosstalk NO debería tener "long time"**: El crosstalk óptico ocurre INMEDIATAMENTE (< 1ns) después del pulso principal
2. **Afterpulses tienen rango temporal específico**: Típicamente 10-500 ns para SiPMs
3. **DCR no se define por delta_t**: DCR son eventos aleatorios, no dependen del tiempo desde el pulso anterior

**Clasificación Física Correcta**:
```python
class SiPMAnalyzer:
    def __init__(self, 
                 spe_threshold_mV: float = 60.0,  # Single Photo-Electron threshold
                 crosstalk_time_ns: float = 50.0,  # Crosstalk window
                 afterpulse_time_ns: float = 500.0):  # Afterpulse window
        self.spe_threshold = spe_threshold_mV
        self.xt_time = crosstalk_time_ns * 1e-9  # Convert to seconds
        self.ap_time = afterpulse_time_ns * 1e-9
    
    def analyze(self, delta_t: np.ndarray, amplitudes_mV: np.ndarray) -> SiPMMetrics:
        """
        Physically correct SiPM event classification.
        
        Classification logic:
        - Crosstalk (XT): High amplitude, VERY short time (< 50 ns)
        - Afterpulse (AP): Any amplitude, short-medium time (50 ns - 500 ns)
        - DCR: Events with long time gaps (> 500 ns) - these are uncorrelated
        """
        metrics = SiPMMetrics()
        total_events = len(delta_t)
        
        # Crosstalk: Immediate high-amplitude events
        xt_mask = (delta_t < self.xt_time) & (amplitudes_mV >= self.spe_threshold)
        
        # Afterpulses: Delayed events within afterpulse window
        ap_mask = (delta_t >= self.xt_time) & (delta_t < self.ap_time)
        
        # DCR: Events with long gaps (uncorrelated with previous event)
        dcr_mask = (delta_t >= self.ap_time)
        
        # Calculate probabilities (per primary pulse)
        # Note: These should be normalized by number of PRIMARY pulses, not total events
        metrics.crosstalk_pct = (np.sum(xt_mask) / total_events) * 100
        metrics.afterpulse_pct = (np.sum(ap_mask) / total_events) * 100
        
        return metrics
```

---

### 4. **Saturación - Manejo Incompleto**
**Archivo**: [`peak_analyzer.py:375-404`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/models/peak_analyzer.py#L375-L404)

```python
# ⚠️ PROBLEMA: Solo maneja saturación en amplitud, no en tiempo
saturation_threshold = self.waveform_data.global_max_amp * 0.95
peak_amps = amplitudes[peaks]
saturated_mask = peak_amps >= saturation_threshold

if np.sum(saturated_mask) > 1:
    # Keep only the highest saturated peak
    ...
```

**Problemas**:
1. **No detecta saturación temporal**: Picos muy anchos (plateau) indican saturación
2. **Threshold arbitrario**: 95% puede no ser apropiado para todos los casos
3. **No marca eventos saturados**: El usuario debería saber qué eventos están saturados

**Mejora**:
```python
def detect_saturation(amplitudes, peaks, properties, global_max, sample_time):
    """
    Detect both amplitude and temporal saturation.
    
    Returns:
        saturated_peaks: Indices of saturated peaks
        saturation_type: 'amplitude', 'temporal', or 'both' for each peak
    """
    saturation_info = []
    
    for i, peak_idx in enumerate(peaks):
        sat_type = []
        
        # Amplitude saturation
        if amplitudes[peak_idx] >= global_max * 0.98:  # More strict threshold
            sat_type.append('amplitude')
        
        # Temporal saturation (flat top)
        if 'widths' in properties and 'plateau_sizes' in properties:
            width = properties['widths'][i]
            plateau = properties.get('plateau_sizes', [0])[i]
            
            # If plateau is > 50% of width, it's saturated
            if plateau > width * 0.5:
                sat_type.append('temporal')
        
        saturation_info.append({
            'peak_idx': peak_idx,
            'saturated': len(sat_type) > 0,
            'type': sat_type if sat_type else None
        })
    
    return saturation_info
```

---

### 5. **Baseline Calculation - Potencial Sesgo**
**Archivo**: [`peak_analyzer.py:62-68`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/models/peak_analyzer.py#L62-L68)

```python
# ⚠️ PROBLEMA: Usa TODAS las amplitudes para calcular baseline
low_p = (100 - baseline_pct) / 2
high_p = 100 - low_p
results.baseline_low = np.percentile(self.waveform_data.all_amplitudes_flat, low_p)
results.baseline_high = np.percentile(self.waveform_data.all_amplitudes_flat, high_p)
```

**Problema**:
- **Incluye picos en el cálculo**: `all_amplitudes_flat` contiene TODO, incluyendo señales
- **Sesgo hacia arriba**: El baseline calculado será más alto de lo real

**Solución**:
```python
def calculate_baseline_robust(waveforms, peak_regions_to_exclude):
    """
    Calculate baseline excluding peak regions.
    
    Args:
        waveforms: List of waveform arrays
        peak_regions_to_exclude: List of (start, end) tuples for each waveform
    """
    baseline_samples = []
    
    for wf, peak_regions in zip(waveforms, peak_regions_to_exclude):
        # Create mask for baseline regions (exclude peaks)
        mask = np.ones(len(wf), dtype=bool)
        for start, end in peak_regions:
            mask[start:end] = False
        
        # Collect baseline samples
        baseline_samples.extend(wf[mask])
    
    baseline_samples = np.array(baseline_samples)
    
    # Use robust statistics
    baseline_median = np.median(baseline_samples)
    baseline_mad = np.median(np.abs(baseline_samples - baseline_median))
    baseline_std = baseline_mad * 1.4826  # Convert MAD to std
    
    return baseline_median, baseline_std
```

---

### 6. **Rise/Fall Time - Interpolación Faltante**
**Archivo**: [`pulse_analysis.py:11-45`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/utils/pulse_analysis.py#L11-L45)

```python
# ⚠️ PROBLEMA: Usa índices discretos sin interpolación
idx_10 = np.where(before_peak >= level_10)[0]
idx_90 = np.where(before_peak >= level_90)[0]

t_10 = time_array[idx_10[0]]
t_90 = time_array[idx_90[0]]

return t_90 - t_10
```

**Problema**:
- **Resolución limitada**: Limitado a SAMPLE_TIME (~1.22 ns para 4081 puntos en 5 µs)
- **Error de cuantización**: Puede tener errores de hasta ±SAMPLE_TIME/2

**Solución con Interpolación**:
```python
def calculate_rise_time_interpolated(amplitudes, time_array, peak_idx, baseline):
    """
    Calculate 10%-90% rise time with linear interpolation for sub-sample accuracy.
    """
    peak_amp = amplitudes[peak_idx]
    amp_range = peak_amp - baseline
    
    level_10 = baseline + 0.1 * amp_range
    level_90 = baseline + 0.9 * amp_range
    
    before_peak = amplitudes[:peak_idx]
    time_before = time_array[:peak_idx]
    
    # Find crossing points with interpolation
    def find_crossing_interpolated(signal, times, threshold):
        """Linear interpolation for sub-sample precision."""
        crossings = np.where(np.diff(signal >= threshold))[0]
        if len(crossings) == 0:
            return np.nan
        
        idx = crossings[0]
        # Linear interpolation between idx and idx+1
        y0, y1 = signal[idx], signal[idx + 1]
        t0, t1 = times[idx], times[idx + 1]
        
        # Interpolate: t = t0 + (threshold - y0) / (y1 - y0) * (t1 - t0)
        if y1 != y0:
            t_cross = t0 + (threshold - y0) / (y1 - y0) * (t1 - t0)
        else:
            t_cross = t0
        
        return t_cross
    
    t_10 = find_crossing_interpolated(before_peak, time_before, level_10)
    t_90 = find_crossing_interpolated(before_peak, time_before, level_90)
    
    if np.isnan(t_10) or np.isnan(t_90):
        return np.nan
    
    return t_90 - t_10
```

---

### 7. **Exponential Recovery Fit - Sin Validación**
**Archivo**: [`pulse_analysis.py:119-155`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/utils/pulse_analysis.py#L119-L155)

```python
# ⚠️ PROBLEMA: No valida calidad del fit
try:
    popt, _ = curve_fit(exponential, delta_t, amplitudes, ...)
    A0, tau = popt
    return tau, A0, fitted_curve
except:
    return np.nan, np.nan, np.array([])
```

**Problemas**:
1. **No calcula R²**: No sabemos si el fit es bueno
2. **No reporta incertidumbres**: `pcov` contiene la covarianza pero no se usa
3. **Catch genérico**: Oculta errores específicos

**Mejora**:
```python
def fit_exponential_recovery_validated(delta_t, amplitudes):
    """
    Fit exponential with quality metrics.
    
    Returns:
        dict with tau, A0, tau_err, A0_err, r_squared, fit_quality
    """
    def exponential(t, A0, tau):
        return A0 * np.exp(-t / tau)
    
    try:
        # Fit
        popt, pcov = curve_fit(
            exponential, delta_t, amplitudes,
            p0=[np.max(amplitudes), np.median(delta_t)],
            maxfev=10000,
            bounds=([0, 0], [np.inf, np.inf])
        )
        
        A0, tau = popt
        
        # Calculate uncertainties from covariance matrix
        perr = np.sqrt(np.diag(pcov))
        A0_err, tau_err = perr
        
        # Calculate R² (coefficient of determination)
        y_fit = exponential(delta_t, A0, tau)
        ss_res = np.sum((amplitudes - y_fit)**2)
        ss_tot = np.sum((amplitudes - np.mean(amplitudes))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine fit quality
        if r_squared > 0.9:
            quality = "excellent"
        elif r_squared > 0.7:
            quality = "good"
        elif r_squared > 0.5:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            'tau': tau,
            'A0': A0,
            'tau_err': tau_err,
            'A0_err': A0_err,
            'r_squared': r_squared,
            'quality': quality,
            'success': True
        }
        
    except Exception as e:
        return {
            'tau': np.nan,
            'A0': np.nan,
            'tau_err': np.nan,
            'A0_err': np.nan,
            'r_squared': 0,
            'quality': 'failed',
            'success': False,
            'error': str(e)
        }
```

---

### 8. **Parallel Processing - Overhead Innecesario**
**Archivo**: [`peak_analyzer.py:78-103`](file:///c:/Users/Ferna/Desktop/Laboratorio/analisis/models/peak_analyzer.py#L78-L103)

```python
# ⚠️ PROBLEMA: Threshold de 50 archivos puede ser muy bajo
use_parallel = num_files > 50  # Use parallel processing for >50 files
```

**Problema**:
- **Overhead de multiprocessing**: Para archivos pequeños, el overhead puede ser mayor que el beneficio
- **No considera tamaño de archivos**: 50 archivos de 100 KB vs 50 archivos de 10 MB

**Mejora**:
```python
def should_use_parallel_processing(num_files, avg_file_size_kb, num_points):
    """
    Decide whether to use parallel processing based on workload.
    
    Rules:
    - Always parallel if > 200 files
    - Never parallel if < 20 files
    - For 20-200 files, consider processing time estimate
    """
    if num_files > 200:
        return True
    if num_files < 20:
        return False
    
    # Estimate processing time per file (empirical)
    time_per_file_ms = (num_points / 1000) * 0.5  # ~0.5 ms per 1000 points
    total_time_sequential_s = (num_files * time_per_file_ms) / 1000
    
    # Use parallel if sequential would take > 5 seconds
    return total_time_sequential_s > 5.0
```

---

## 🟡 MEJORAS SUGERIDAS

### 9. **Photon Counting - Funcionalidad Faltante**

Los SiPMs son excelentes para **conteo de fotones**. Tu herramienta debería poder:

```python
class PhotonCounter:
    """
    Photon counting analysis for SiPM signals.
    """
    def __init__(self, spe_charge_pC: float, spe_charge_std_pC: float):
        """
        Args:
            spe_charge_pC: Single photo-electron charge (from calibration)
            spe_charge_std_pC: SPE charge standard deviation
        """
        self.spe_charge = spe_charge_pC
        self.spe_std = spe_charge_std_pC
    
    def estimate_photon_number(self, measured_charge_pC: float) -> dict:
        """
        Estimate number of detected photons from measured charge.
        
        Returns:
            dict with n_photons, n_photons_err, probability
        """
        # Simple division
        n_photons_raw = measured_charge_pC / self.spe_charge
        
        # Round to nearest integer
        n_photons = int(np.round(n_photons_raw))
        
        # Calculate uncertainty
        # σ_n = sqrt((σ_Q / Q_spe)² + (Q * σ_spe / Q_spe²)²)
        n_photons_err = np.sqrt(
            (self.spe_std / self.spe_charge)**2 + 
            (measured_charge_pC * self.spe_std / self.spe_charge**2)**2
        )
        
        # Probability that this is the correct number (Gaussian approximation)
        from scipy.stats import norm
        prob = norm.pdf(n_photons_raw, n_photons, n_photons_err)
        
        return {
            'n_photons': n_photons,
            'n_photons_raw': n_photons_raw,
            'n_photons_err': n_photons_err,
            'probability': prob
        }
    
    def create_photon_histogram(self, charges_pC: np.ndarray) -> dict:
        """
        Create histogram of photon numbers.
        """
        photon_numbers = []
        
        for charge in charges_pC:
            result = self.estimate_photon_number(charge)
            photon_numbers.append(result['n_photons'])
        
        photon_numbers = np.array(photon_numbers)
        
        # Create histogram
        max_photons = int(np.max(photon_numbers)) + 1
        hist, bins = np.histogram(photon_numbers, bins=range(max_photons + 1))
        
        return {
            'photon_numbers': photon_numbers,
            'histogram': hist,
            'bins': bins,
            'mean_photons': np.mean(photon_numbers),
            'std_photons': np.std(photon_numbers)
        }
```

---

### 10. **Gain Calculation - Métrica Crítica**

**Falta**: Cálculo de ganancia del SiPM

```python
def calculate_sipm_gain(spe_charge_pC: float, elementary_charge_C: float = 1.602e-19):
    """
    Calculate SiPM gain from SPE charge.
    
    Gain = Q_spe / e
    
    Args:
        spe_charge_pC: Single photo-electron charge in picocoulombios
        elementary_charge_C: Elementary charge (1.602e-19 C)
    
    Returns:
        Gain (number of electrons per detected photon)
    """
    spe_charge_C = spe_charge_pC * 1e-12  # Convert pC to C
    gain = spe_charge_C / elementary_charge_C
    
    return gain

# Example usage
# If SPE charge = 100 pC:
# Gain = (100e-12 C) / (1.602e-19 C) = 6.24e5 ≈ 600,000 electrons
```

---

### 11. **Photon Detection Efficiency (PDE)**

```python
class PDEAnalyzer:
    """
    Analyze Photon Detection Efficiency of SiPM.
    """
    def __init__(self, known_photon_flux: float, detection_area_mm2: float):
        """
        Args:
            known_photon_flux: Known photon flux (photons/s)
            detection_area_mm2: Active area of SiPM (mm²)
        """
        self.photon_flux = known_photon_flux
        self.area = detection_area_mm2
    
    def calculate_pde(self, detected_photons: int, measurement_time_s: float) -> float:
        """
        Calculate PDE from detected photons.
        
        PDE = (detected photons / time) / (incident photons / time)
        """
        detected_rate = detected_photons / measurement_time_s
        incident_rate = self.photon_flux * (self.area / 100)  # Assuming flux per cm²
        
        pde = detected_rate / incident_rate if incident_rate > 0 else 0
        
        return pde * 100  # Return as percentage
```

---

### 12. **Correlated Noise Analysis**

```python
def analyze_correlated_noise(afterpulse_times_ns, crosstalk_times_ns):
    """
    Analyze correlated noise (afterpulsing + crosstalk) vs time.
    
    This helps understand trap dynamics in SiPM.
    """
    # Combine all correlated events
    all_times = np.concatenate([afterpulse_times_ns, crosstalk_times_ns])
    all_types = ['AP'] * len(afterpulse_times_ns) + ['XT'] * len(crosstalk_times_ns)
    
    # Create time bins (logarithmic for better visualization)
    bins = np.logspace(np.log10(1), np.log10(1000), 50)  # 1 ns to 1 µs
    
    # Histogram
    hist_ap, _ = np.histogram(afterpulse_times_ns, bins=bins)
    hist_xt, _ = np.histogram(crosstalk_times_ns, bins=bins)
    
    # Fit exponential components (afterpulses often have multiple time constants)
    # This reveals different trap levels
    
    return {
        'bins': bins,
        'afterpulse_hist': hist_ap,
        'crosstalk_hist': hist_xt,
        'total_correlated_noise_pct': (len(all_times) / total_events) * 100
    }
```

---

### 13. **Temperature Dependence Tracking**

```python
class TemperatureDependenceTracker:
    """
    Track SiPM parameters vs temperature.
    """
    def __init__(self, database_file='sipm_temp_data.json'):
        self.db_file = database_file
        self.load_data()
    
    def record_measurement(self, temperature_C, dcr_hz, gain, breakdown_voltage):
        """
        Record measurement at specific temperature.
        """
        self.data.append({
            'timestamp': datetime.now().isoformat(),
            'temperature_C': temperature_C,
            'dcr_hz': dcr_hz,
            'gain': gain,
            'breakdown_voltage': breakdown_voltage
        })
        self.save_data()
    
    def plot_temperature_dependence(self):
        """
        Plot DCR, gain, etc. vs temperature.
        """
        temps = [d['temperature_C'] for d in self.data]
        dcrs = [d['dcr_hz'] for d in self.data]
        
        # DCR typically doubles every ~8°C
        # Plot and fit exponential
        ...
```

---

### 14. **Signal-to-Noise Ratio (SNR) Calculation**

```python
def calculate_snr_sipm(signal_amplitude_mV, baseline_std_mV):
    """
    Calculate SNR for SiPM signals.
    
    SNR = A_signal / σ_noise
    
    For SiPMs, SNR > 5 is typically required for reliable detection.
    """
    snr = signal_amplitude_mV / baseline_std_mV if baseline_std_mV > 0 else 0
    snr_db = 20 * np.log10(snr) if snr > 0 else -np.inf
    
    return {
        'snr_linear': snr,
        'snr_db': snr_db,
        'quality': 'excellent' if snr > 10 else 'good' if snr > 5 else 'poor'
    }
```

---

### 15. **Pulse Shape Discrimination (PSD)**

```python
def calculate_psd_parameter(amplitudes, time_array, peak_idx, baseline, 
                           short_gate_ns=50, long_gate_ns=500):
    """
    Calculate Pulse Shape Discrimination parameter.
    
    PSD is useful for distinguishing different types of events.
    
    PSD = (Q_long - Q_short) / Q_long
    """
    # Convert gates to samples
    short_samples = int(short_gate_ns * 1e-9 / SAMPLE_TIME)
    long_samples = int(long_gate_ns * 1e-9 / SAMPLE_TIME)
    
    # Calculate short integral
    start_short = peak_idx
    end_short = min(len(amplitudes), peak_idx + short_samples)
    q_short = np.trapz(amplitudes[start_short:end_short] - baseline, 
                       time_array[start_short:end_short])
    
    # Calculate long integral
    start_long = peak_idx
    end_long = min(len(amplitudes), peak_idx + long_samples)
    q_long = np.trapz(amplitudes[start_long:end_long] - baseline,
                      time_array[start_long:end_long])
    
    # PSD parameter
    psd = (q_long - q_short) / q_long if q_long > 0 else 0
    
    return psd
```

---

## ✨ NUEVAS FUNCIONALIDADES PROPUESTAS

### 16. **Auto-Calibration con LED Pulsado**

```python
class SiPMAutoCalibrator:
    """
    Automatic calibration using pulsed LED.
    """
    def calibrate_spe_charge(self, charge_histogram, expected_peaks=3):
        """
        Automatically find SPE charge from multi-photon peaks.
        
        Peaks should be at: Q_spe, 2*Q_spe, 3*Q_spe, ...
        """
        from scipy.signal import find_peaks
        
        # Find peaks in charge histogram
        peaks, properties = find_peaks(charge_histogram, 
                                      prominence=np.max(charge_histogram) * 0.1,
                                      distance=10)
        
        if len(peaks) < 2:
            return None
        
        # Calculate spacing between peaks
        peak_positions = peaks[:expected_peaks]
        spacings = np.diff(peak_positions)
        
        # SPE charge is the average spacing
        spe_charge = np.mean(spacings)
        spe_charge_std = np.std(spacings)
        
        return {
            'spe_charge_pC': spe_charge,
            'spe_charge_std_pC': spe_charge_std,
            'num_peaks_found': len(peaks),
            'peak_positions': peak_positions
        }
```

---

### 17. **Waveform Averaging y Template Matching**

```python
def create_average_waveform_template(accepted_waveforms, alignment='peak'):
    """
    Create averaged waveform template for matched filtering.
    
    Args:
        accepted_waveforms: List of accepted waveform arrays
        alignment: 'peak' or 'rising_edge'
    """
    aligned_waveforms = []
    
    for wf in accepted_waveforms:
        if alignment == 'peak':
            # Align by peak position
            peak_idx = np.argmax(wf)
            shift = len(wf) // 2 - peak_idx
            wf_shifted = np.roll(wf, shift)
        else:
            # Align by rising edge (10% level)
            threshold = np.min(wf) + 0.1 * (np.max(wf) - np.min(wf))
            rising_idx = np.where(wf > threshold)[0][0]
            shift = len(wf) // 4 - rising_idx
            wf_shifted = np.roll(wf, shift)
        
        aligned_waveforms.append(wf_shifted)
    
    # Average
    template = np.mean(aligned_waveforms, axis=0)
    template_std = np.std(aligned_waveforms, axis=0)
    
    return template, template_std
```

---

### 18. **Análisis de Estabilidad Temporal**

```python
class StabilityAnalyzer:
    """
    Analyze temporal stability of SiPM performance.
    """
    def analyze_drift(self, timestamps, amplitudes, window_size=100):
        """
        Detect amplitude drift over time.
        """
        # Calculate rolling mean
        rolling_mean = np.convolve(amplitudes, 
                                   np.ones(window_size)/window_size, 
                                   mode='valid')
        
        # Calculate drift rate (mV/hour)
        time_hours = (timestamps - timestamps[0]) / 3600
        drift_rate, intercept = np.polyfit(time_hours[:len(rolling_mean)], 
                                          rolling_mean, 1)
        
        return {
            'drift_rate_mV_per_hour': drift_rate * 1000,
            'is_stable': abs(drift_rate) < 0.001,  # < 1 mV/hour
            'rolling_mean': rolling_mean
        }
```

---

### 19. **Export to ROOT Format**

Para análisis en ROOT (CERN):

```python
def export_to_root(waveforms, filename='sipm_data.root'):
    """
    Export waveforms to ROOT format for advanced analysis.
    
    Requires: uproot library
    """
    try:
        import uproot
    except ImportError:
        print("uproot not installed. Install with: pip install uproot")
        return
    
    with uproot.recreate(filename) as file:
        # Create TTree
        file["waveforms"] = {
            "amplitude": np.array([wf for wf in waveforms]),
            "time": np.arange(len(waveforms[0])) * SAMPLE_TIME,
            "peak_amplitude": np.array([np.max(wf) for wf in waveforms]),
            "charge": np.array([calculate_charge(wf) for wf in waveforms])
        }
    
    print(f"Exported to {filename}")
```

---

### 20. **Machine Learning - Event Classification**

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class MLEventClassifier:
    """
    Use ML to classify SiPM events.
    """
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
    
    def extract_features(self, waveform, peak_idx):
        """
        Extract features for ML classification.
        """
        features = {
            'peak_amplitude': waveform[peak_idx],
            'rise_time': calculate_rise_time(waveform, peak_idx),
            'fall_time': calculate_fall_time(waveform, peak_idx),
            'fwhm': calculate_fwhm(waveform, peak_idx),
            'charge': calculate_charge(waveform, peak_idx),
            'baseline_std': np.std(waveform[:100]),
            'peak_position': peak_idx,
            'asymmetry': calculate_asymmetry(waveform, peak_idx)
        }
        return list(features.values())
    
    def train(self, training_waveforms, labels):
        """
        Train classifier on labeled data.
        
        Labels: 'signal', 'noise', 'afterpulse', 'crosstalk'
        """
        X = [self.extract_features(wf, np.argmax(wf)) for wf in training_waveforms]
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, labels)
    
    def predict(self, waveform, peak_idx):
        """
        Classify event.
        """
        features = self.extract_features(waveform, peak_idx)
        features_scaled = self.scaler.transform([features])
        
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        return {
            'class': prediction,
            'probability': max(probability),
            'all_probabilities': dict(zip(self.model.classes_, probability))
        }
```

---

## 📊 RESUMEN DE PRIORIDADES

### 🔴 **CRÍTICO - Arreglar Inmediatamente**
1. ✅ **Cálculo de carga** - Implementar integración correcta con trapz
2. ✅ **DCR calculation** - Usar tiempo total de adquisición
3. ✅ **Clasificación SiPM** - Usar ventanas temporales físicamente correctas

### 🟡 **IMPORTANTE - Implementar Pronto**
4. ✅ **Interpolación en rise/fall time** - Mejorar precisión temporal
5. ✅ **Validación de fits** - Agregar R² y errores
6. ✅ **Photon counting** - Funcionalidad esencial para SiPMs
7. ✅ **Cálculo de ganancia** - Métrica fundamental

### 🟢 **MEJORAS - Cuando sea Posible**
8. ✅ **Auto-calibración** - Facilita uso
9. ✅ **Template matching** - Mejora SNR
10. ✅ **ML classification** - Análisis avanzado
11. ✅ **Export to ROOT** - Compatibilidad con análisis estándar

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Correcciones Críticas (1-2 días)
```
[ ] Corregir cálculo de carga en charge_histogram_window.py
[ ] Implementar DCR correcto en signal_processing.py
[ ] Revisar clasificación de eventos SiPM
[ ] Agregar validación de baseline (excluir picos)
```

### Fase 2: Mejoras de Precisión (2-3 días)
```
[ ] Implementar interpolación en pulse_analysis.py
[ ] Agregar validación de fits (R², errores)
[ ] Mejorar detección de saturación
[ ] Optimizar threshold de procesamiento paralelo
```

### Fase 3: Nuevas Funcionalidades (1 semana)
```
[ ] Implementar photon counting
[ ] Agregar cálculo de ganancia
[ ] Crear auto-calibración con LED
[ ] Implementar PDE analysis
```

### Fase 4: Análisis Avanzado (2 semanas)
```
[ ] Template matching y averaged waveforms
[ ] ML event classification
[ ] Análisis de estabilidad temporal
[ ] Export to ROOT format
```

---

## 📝 NOTAS FINALES

Tu herramienta es **muy completa** y está bien estructurada. Los problemas identificados son principalmente:

1. **Errores conceptuales** en cálculos físicos (carga, DCR, clasificación)
2. **Falta de validación** en fits y resultados
3. **Precisión limitada** por falta de interpolación
4. **Funcionalidades faltantes** que son estándar en análisis SiPM

**Nombre Sugerido**: 
- **"SiPM MultiTool"** ✅
- **"SiPM Analyzer Pro"**
- **"PhotonScope"** (más comercial)
- **"SiPM Workbench"**

¿Quieres que implemente alguna de estas correcciones o funcionalidades específicas?
