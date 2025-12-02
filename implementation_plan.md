# Plan de Implementación: Análisis Avanzado y Procesamiento de Señal

## Objetivo

Reorganizar la UI del sidebar y añadir dos nuevas ventanas de análisis:
1. **Análisis Avanzado SiPM**: Recovery time, jitter temporal, pulse shape analysis
2. **Procesamiento de Señal**: Filtros digitales con preview y aplicación permanente

---

## Cambios Propuestos

### 1. Reorganización del Sidebar

**Problema actual**: Los botones no caben en el sidebar.

**Solución**: Crear un grid 2x4 (2 columnas x 4 filas) con todos los botones juntos.

**Layout propuesto**:
```
┌─────────────────────────────┐
│  ANÁLISIS Y VISUALIZACIÓN   │
├──────────────┬──────────────┤
│ Actualizar   │ Guardar      │  ← Fila 1
│              │ conf         │
├──────────────┼──────────────┤
│ Ver dist.    │ Ver wf       │  ← Fila 2
│ temporal     │ completo     │
├──────────────┼──────────────┤
│ Ver hist.    │ Ver análisis │  ← Fila 3
│ carga        │ avanzado     │
├──────────────┼──────────────┤
│ Filtros      │ Exportar     │  ← Fila 4
│              │              │
└──────────────┴──────────────┘
```

---

## 2. Ventana: Análisis Avanzado SiPM

### Archivo
`views/popups/advanced_sipm_analysis_window.py`

### Funcionalidades

#### 2.1 Recovery Time Analysis
**Objetivo**: Caracterizar tiempo de recuperación del SiPM después de un pulso.

**Implementación**:
- Extraer afterpulses de waveforms con múltiples picos
- Calcular Δt entre pulso principal y afterpulses
- Graficar amplitud vs Δt
- Ajuste exponencial: `A(t) = A0 * exp(-t/τ)`
- Mostrar constante de tiempo τ

**Plot**:
```
Amplitud (mV)
    │     ●
    │    ●  ●
    │   ●    ●
    │  ●      ●
    │ ●        ●___
    └─────────────────── Δt (µs)
      Ajuste: τ = 2.3 µs
```

#### 2.2 Jitter Temporal
**Objetivo**: Medir resolución temporal del detector.

**Implementación**:
- Extraer tiempos de pico principal de waveforms aceptadas
- Calcular histograma de tiempos
- Ajuste gaussiano
- Calcular FWHM y RMS jitter
- Correlación amplitud vs jitter

**Plots**:
1. Histograma de tiempos con ajuste gaussiano
2. Scatter plot: Amplitud vs Tiempo de pico

#### 2.3 Pulse Shape Analysis
**Objetivo**: Caracterizar forma del pulso.

**Implementación**:
- Extraer parámetros de cada pulso:
  - Rise time (10%-90%)
  - Fall time (90%-10%)
  - FWHM (Full Width Half Maximum)
  - Área integrada
  - Ratio área/amplitud
- Promediado de pulsos para template
- PCA para clasificación de formas
- Detección de anomalías

**Plots**:
1. Pulso promedio con anotaciones (rise/fall time)
2. Histogramas de parámetros
3. Scatter plots de correlaciones
4. PCA components (2D projection)

### UI Layout
```
┌─────────────────────────────────────────────┐
│  Análisis Avanzado SiPM                  [X]│
├─────────────────────────────────────────────┤
│  [Recovery Time] [Jitter] [Pulse Shape]     │ ← Tabs
├─────────────────────────────────────────────┤
│                                             │
│         [Gráfico Principal]                 │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│  Resultados:                                │
│  • τ recovery = 2.34 ± 0.12 µs             │
│  • Jitter RMS = 45 ps                       │
│  • Rise time = 3.2 ± 0.5 ns                │
├─────────────────────────────────────────────┤
│         [Exportar Resultados]               │
└─────────────────────────────────────────────┘
```

---

## 3. Ventana: Procesamiento de Señal

### Archivo
`views/popups/signal_processing_window.py`

### Funcionalidades

#### 3.1 Filtros Disponibles

**Savitzky-Golay**:
- Parámetros: window_length, polyorder
- Suavizado preservando picos

**Matched Filter**:
- Template: pulso promedio
- Convolución para mejorar SNR

**Wiener Filter**:
- Estimación de ruido automática
- Filtrado adaptativo

**Wavelet Denoising**:
- Wavelet: db4, sym4, coif3
- Threshold automático o manual

#### 3.2 UI Interactiva

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│  Procesamiento de Señal Avanzado                      [X]│
├──────────────────────────────────────────────────────────┤
│  Filtro: [Savitzky-Golay ▼]                              │
│                                                           │
│  Parámetros:                                              │
│  Window Length: [11] ───────○───────                      │
│  Poly Order:    [3]  ───○───────────                      │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────────────┬─────────────────────┐           │
│  │   ANTES             │   DESPUÉS           │           │
│  │                     │                     │           │
│  │   [Waveform         │   [Waveform         │           │
│  │    Original]        │    Filtrada]        │           │
│  │                     │                     │           │
│  │                     │                     │           │
│  └─────────────────────┴─────────────────────┘           │
│                                                           │
│  Waveform: SiPMG_LAr_DCR1_0001.txt                       │
│  SNR mejora: +3.2 dB                                      │
│                                                           │
│  [◄ Anterior]  [Siguiente ►]                              │
├──────────────────────────────────────────────────────────┤
│  [Aplicar a Todas]  [Cancelar]                            │
└──────────────────────────────────────────────────────────┘
```

#### 3.3 Flujo de Aplicación

**Cuando el usuario presiona "Aplicar a Todas"**:

1. **Crear directorio nuevo**:
   ```
   Original: SiPMG_LAr_DCR1_AMP/
   Filtrado: SiPMG_LAr_DCR1_AMP-SavitzkyGolay/
   ```

2. **Procesar todos los archivos**:
   - Leer cada archivo del directorio original
   - Aplicar filtro seleccionado con parámetros
   - Guardar en nuevo directorio con mismo nombre
   - Mostrar progress bar

3. **Actualizar configuración**:
   - Mostrar diálogo: "¿Usar datos filtrados para próximo análisis?"
   - Si sí: Actualizar `user_config.json` con nuevo DATA_DIR
   - Si no: Mantener configuración actual

4. **Recargar análisis** (opcional):
   - Ofrecer re-analizar con datos filtrados inmediatamente

---

## Implementación Técnica

### Archivos a Crear

#### 1. `views/popups/advanced_sipm_analysis_window.py`
```python
class AdvancedSiPMAnalysisWindow(BasePopup):
    """Window for advanced SiPM characterization."""
    
    def __init__(self, parent, results):
        # Tabs: Recovery Time, Jitter, Pulse Shape
        
    def analyze_recovery_time(self):
        # Extract afterpulses, fit exponential
        
    def analyze_jitter(self):
        # Histogram of peak times, gaussian fit
        
    def analyze_pulse_shape(self):
        # Extract rise/fall times, PCA
```

#### 2. `views/popups/signal_processing_window.py`
```python
class SignalProcessingWindow(BasePopup):
    """Window for signal filtering with preview."""
    
    def __init__(self, parent, waveform_data):
        # Filter selection, parameter controls
        # Before/after plots
        # Navigation buttons
        
    def apply_filter(self, amplitudes):
        # Apply selected filter with current params
        
    def apply_to_all(self):
        # Create new directory
        # Process all files
        # Update config
```

#### 3. `utils/signal_filters.py`
```python
def savitzky_golay_filter(amplitudes, window_length, polyorder):
    """Apply Savitzky-Golay filter."""
    
def matched_filter(amplitudes, template):
    """Apply matched filter."""
    
def wiener_filter(amplitudes, noise_estimate):
    """Apply Wiener filter."""
    
def wavelet_denoise(amplitudes, wavelet, threshold):
    """Apply wavelet denoising."""
```

#### 4. `utils/pulse_analysis.py`
```python
def calculate_rise_time(amplitudes, time_array):
    """Calculate 10%-90% rise time."""
    
def calculate_fall_time(amplitudes, time_array):
    """Calculate 90%-10% fall time."""
    
def calculate_fwhm(amplitudes, time_array):
    """Calculate Full Width Half Maximum."""
    
def fit_exponential_recovery(delta_t, amplitudes):
    """Fit exponential to recovery time data."""
```

### Archivos a Modificar

#### 1. `views/control_sidebar.py`
- Crear grid 2x4 (2 columnas x 4 filas) para todos los botones
- Añadir botón "Guardar conf" para guardar configuración
- Añadir callbacks para nuevas ventanas

#### 2. `views/popups/__init__.py`
- Importar nuevas ventanas
- Exportar funciones `show_advanced_sipm_analysis` y `show_signal_processing`

#### 3. `views/main_window.py`
- Conectar nuevos botones a callbacks
- Pasar datos necesarios a nuevas ventanas

#### 4. `config.py`
- Añadir configuración para filtros por defecto
- Parámetros de filtros

#### 5. `utils/config_manager.py`
- Método para actualizar DATA_DIR
- Guardar historial de directorios filtrados

---

## Dependencias Adicionales

```python
# Para filtros avanzados
scipy.signal.savgol_filter  # Savitzky-Golay
scipy.signal.wiener  # Wiener filter
pywt  # PyWavelets para wavelet denoising
sklearn.decomposition.PCA  # Para pulse shape PCA
```

Añadir a requirements:
```
pywavelets>=1.4.0
scikit-learn>=1.3.0
```

---

## Priorización de Implementación

### Fase 1 (Esencial) - 4-6 horas
1. [ ] Reorganizar sidebar con grid 2x4 (2 columnas x 4 filas)
2. [ ] Crear `signal_processing_window.py` básica
3. [ ] Implementar Savitzky-Golay filter
4. [ ] Implementar preview antes/después
5. [ ] Implementar "Aplicar a Todas" con creación de directorio

### Fase 2 (Importante) - 3-4 horas
6. [ ] Añadir resto de filtros (Matched, Wiener, Wavelet)
7. [ ] Crear `advanced_sipm_analysis_window.py`
8. [ ] Implementar Recovery Time analysis

### Fase 3 (Complementaria) - 2-3 horas
9. [ ] Implementar Jitter analysis
10. [ ] Implementar Pulse Shape analysis
11. [ ] Añadir exportación de resultados

---

## Consideraciones de Diseño

### Performance
- Filtrado puede ser lento para muchos archivos
- Usar procesamiento paralelo (ProcessPoolExecutor)
- Mostrar progress bar detallado
- Permitir cancelación

### UX
- Preview interactivo antes de aplicar
- Validación de parámetros en tiempo real
- Tooltips explicativos para cada filtro
- Undo/Redo no necesario (datos originales intactos)

### Almacenamiento
- No sobrescribir datos originales nunca
- Nomenclatura clara: `{original}-{filter}-{params}`
- Metadata JSON con parámetros usados
- Opción de limpiar directorios filtrados antiguos

---

## Testing

### Test Cases
1. Aplicar cada filtro a waveform de prueba
2. Verificar que archivos se crean correctamente
3. Verificar que config se actualiza
4. Verificar que análisis funciona con datos filtrados
5. Verificar navegación entre waveforms en preview
6. Verificar cancelación de procesamiento

### Validación
- Comparar SNR antes/después
- Verificar que picos se preservan
- Verificar que no hay artefactos
- Comparar con implementaciones de referencia (scipy)

---

## Próximos Pasos

1. ¿Aprobar este plan?
2. Comenzar con Fase 1: Reorganización UI + Signal Processing básico
3. Iterar y añadir funcionalidades
