

#### 6. **Filtrado y Búsqueda de Waveforms**
**Funcionalidad**: Buscar waveforms específicas por criterios.

**Criterios de búsqueda**:
- Rango de amplitud
- Número de picos
- Tiempo del pico principal
- Categoría (accepted/rejected/afterpulse)
- Nombre de archivo (regex)

**UI propuesta**:
```
[🔍 Buscar]
Amplitud: [min] - [max] mV
Picos: [=] [1] ▼
Categoría: [Todos ▼]
[Aplicar Filtro]
```

---

#### 7. **Comparación de Análisis**
**Funcionalidad**: Comparar resultados con diferentes parámetros lado a lado.

**Características**:
- Guardar múltiples configuraciones de parámetros
- Vista comparativa de métricas
- Gráficos de diferencias
- Exportar tabla comparativa

**Ejemplo**:
```
Configuración A vs B:
- Accepted: 1234 vs 1189 (↓ 3.6%)
- Afterpulse: 456 vs 478 (↑ 4.8%)
- DCR: 245.3 Hz vs 251.2 Hz (↑ 2.4%)
```

---

### Prioridad Media

#### 8. **Histogramas y Estadísticas Avanzadas**
**Funcionalidad**: Visualizaciones estadísticas adicionales.

**Gráficos propuestos**:
- Histograma de amplitudes
- Histograma de tiempos de pico
- Distribución de anchos de pico
- Correlación amplitud vs tiempo
- Box plots por categoría

---

#### 9. **Detección de Anomalías**
**Funcionalidad**: Identificar waveforms atípicas automáticamente.

**Métodos**:
- Isolation Forest para outliers
- Z-score para valores extremos
- Clustering (DBSCAN) para patrones inusuales

**UI**:
```
⚠️ Anomalías detectadas: 23 waveforms
- 12 con amplitud inusual
- 8 con múltiples picos saturados
- 3 con ruido excesivo
[Ver Detalles]
```

---

## 🎨 Mejoras de Interfaz de Usuario

### Alta Prioridad

#### 13. **Indicador de Progreso**
**Problema actual**: No hay feedback durante análisis largos.

**Solución propuesta**:
```python
import tkinter.ttk as ttk

class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, total_files):
        self.progress_bar = ttk.Progressbar(
            self, maximum=total_files
        )
        self.label = ctk.CTkLabel(
            self, text="Analizando..."
        )
```

**Información a mostrar**:
- Barra de progreso (%)
- Archivos procesados / total
- Tiempo estimado restante
- Botón de cancelar

---

## 🔬 Análisis Avanzado

### Alta Prioridad

#### 19. **Análisis de Correlación Temporal**
**Funcionalidad**: Estudiar correlaciones entre eventos consecutivos.

**Métricas**:
- Autocorrelación de tiempos entre picos
- Detección de periodicidades
- Análisis de Fourier de la serie temporal

**Visualización**:
- Gráfico de autocorrelación
- Espectro de frecuencias
- Periodograma

---

#### 20. **Caracterización Completa de SiPM**
**Funcionalidad**: Calcular todas las métricas estándar de SiPM.

**Métricas adicionales**:
- **PDE (Photon Detection Efficiency)**: Si se conoce el flujo de fotones
- **Gain**: Amplificación del SiPM
- **ENF (Excess Noise Factor)**: Factor de ruido
- **Recovery Time**: Tiempo de recuperación
- **Optical Crosstalk Probability**: Probabilidad de crosstalk óptico

---

### Prioridad Media

#### 21. **Ajuste de Distribuciones Estadísticas**
**Funcionalidad**: Ajustar modelos estadísticos a los datos.

**Distribuciones**:
- Poisson para DCR
- Exponencial para intervalos de tiempo
- Gaussiana para amplitudes

**Visualización**:
- Histograma + curva ajustada
- Parámetros del ajuste
- Bondad de ajuste (χ², R²)

---

## 📊 Exportación y Reportes

### Alta Prioridad

#### 24. **Reporte PDF Automático**
**Funcionalidad**: Generar reporte profesional en PDF.

**Contenido**:
- Resumen ejecutivo con métricas clave
- Gráficos principales (distribución temporal, histogramas)
- Tabla de parámetros utilizados
- Estadísticas por categoría
- Ejemplos de waveforms representativas

**Librería sugerida**: `reportlab` o `matplotlib.backends.backend_pdf`

---

#### 25. **Exportación de Gráficos**
**Funcionalidad**: Guardar gráficos individuales en alta resolución.

**Formatos**:
- PNG (alta resolución, 300 DPI)
- SVG (vectorial, para publicaciones)
- PDF (para documentos)

**Características**:
- Botón "Exportar" en cada gráfico
- Configuración de DPI
- Selección de tamaño

---

## 🏗️ Arquitectura y Código

#### 29. **Manejo de Errores Robusto**
**Problema actual**: Algunos errores se silencian con `try/except` genéricos.

**Mejoras**:
```python
class WaveformError(Exception):
    """Error específico de waveform"""
    pass

class AnalysisError(Exception):
    """Error durante análisis"""
    pass

# Usar excepciones específicas
try:
    result = analyze_waveform(file)
except WaveformError as e:
    logger.error(f"Error en {file}: {e}")
    # Mostrar diálogo al usuario
    show_error_dialog(str(e))
```

---

#### 30. **Configuración Externalizada**
**Problema actual**: Configuración hardcodeada en `config.py`.

**Solución propuesta**:
```python
# config.yaml
data:
  directory: "C:/Users/Ferna/Desktop/Laboratorio/analisis/SiPMG_LAr_DCR1_AMP"
  pattern: "SiPMG_LAr_DCR1_*.txt"

analysis:
  defaults:
    prominence_pct: 2.0
    width_time: 0.2e-6
    
ui:
  theme: "Dark"
  window_size: "1600x900"
```

**Beneficios**:
- Configuración sin recompilar
- Múltiples perfiles (desarrollo, producción)
- Más fácil para usuarios no técnicos

---

#### 32. **Refactorización de popup_windows.py**
**Problema actual**: Archivo grande (18KB) con múltiples responsabilidades.

**Solución propuesta**:
```
views/
├── popups/
│   ├── temporal_distribution_window.py
│   ├── all_waveforms_window.py
│   └── base_popup.py
```

**Beneficios**:
- Código más mantenible
- Reutilización de componentes
- Más fácil de testear

---

#### 33. **Utilidades Compartidas**
**Funcionalidad**: Crear módulo `utils/` con funciones comunes.

**Contenido propuesto**:
```
utils/
├── __init__.py
├── file_io.py          # Lectura/escritura de archivos
├── signal_processing.py # Funciones de procesamiento de señal
├── plotting.py         # Helpers para gráficos
└── validators.py       # Validación de parámetros
```

---