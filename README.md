# SiPM Waveform Analyzer

Aplicación de escritorio para el análisis automatizado de señales de fotomultiplicadores de silicio (SiPM) en experimentos de física de partículas. Desarrollada para el análisis de Dark Count Rate (DCR) y caracterización de SiPMs en condiciones criogénicas.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Características Principales](#características-principales)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Guía de Uso](#guía-de-uso)
- [Arquitectura del Software](#arquitectura-del-software)
- [Algoritmo de Análisis](#algoritmo-de-análisis)
- [Formato de Datos](#formato-de-datos)
- [Configuración](#configuración)
- [Contribuir](#contribuir)

---

## 🔬 Descripción General

Este software analiza automáticamente miles de formas de onda (waveforms) capturadas por un osciloscopio digital, identificando y clasificando pulsos individuales de fotones detectados por SiPMs. El programa implementa algoritmos avanzados de detección de picos, filtrado de ruido, y clasificación estadística para caracterizar el comportamiento del detector.

### Contexto Científico

Los SiPMs (Silicon Photomultipliers) son detectores de luz extremadamente sensibles utilizados en:
- Experimentos de física de partículas
- Detección de neutrinos
- Tomografía por emisión de positrones (PET)
- Experimentos de materia oscura

Este software permite analizar el **Dark Count Rate (DCR)** - la tasa de pulsos espurios generados térmicamente en ausencia de luz - un parámetro crítico para caracterizar la calidad del detector.

---

## ✨ Características Principales

### Análisis Automatizado
- **Detección de picos**: Algoritmo basado en `scipy.signal.find_peaks` con parámetros configurables
- **Clasificación automática**: Separa señales en tres categorías:
  - **Aceptados**: Pulsos únicos bien formados (candidatos a fotoelectrones individuales)
  - **Afterpulse**: Múltiples pulsos en una ventana temporal (indicativo de afterpulsing)
  - **Rechazados**: Señales fuera de los criterios de calidad
- **Procesamiento paralelo**: Análisis multihilo para datasets grandes (>50 archivos)
- **Caché inteligente**: Guarda resultados para evitar reprocesamiento

### Visualización Interactiva
- **Navegación por categorías**: Explora waveforms clasificados con controles de navegación
- **Plots sincronizados**: Visualiza simultáneamente señales aceptadas, rechazadas y afterpulse
- **Zonas de análisis**: Representación visual de baseline, zona de máximos, y afterpulse
- **Sistema de favoritos**: Marca y guarda waveforms de interés para análisis posterior

### Análisis Avanzado
- **Distribución temporal**: Scatter plot de frecuencia vs amplitud
- **Procesamiento de señal**: FFT, filtros pasa-bajos, análisis de ruido
- **Histogramas de carga**: Distribución de carga integrada de pulsos
- **Comparación de datasets**: Compara dos conjuntos de datos lado a lado

### Optimizaciones de Rendimiento
- **UI no bloqueante**: Threading para mantener la interfaz responsiva durante análisis largos
- **I/O optimizado**: Lectura única de archivos con estadísticas calculadas en memoria
- **Muestreo adaptativo**: Visualización eficiente de miles de waveforms superpuestos

---

## 💻 Requisitos del Sistema

### Software
- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows 10/11, macOS, o Linux

### Dependencias Python
```
customtkinter >= 5.0.0    # Interfaz gráfica moderna
matplotlib >= 3.5.0        # Visualización de datos
numpy >= 1.21.0            # Operaciones numéricas
scipy >= 1.7.0             # Procesamiento de señales
```

### Hardware Recomendado
- **RAM**: Mínimo 4 GB (8 GB recomendado para datasets >10,000 waveforms)
- **CPU**: Procesador multi-core para aprovechar paralelización
- **Almacenamiento**: Espacio suficiente para datos (~1 MB por 1000 waveforms)

---

## 🚀 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/FernandoFGF/sipm-waveform-analyzer/
cd analisis
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install customtkinter matplotlib numpy scipy
```

### 4. Ejecutar la Aplicación
```bash
python main.py
```

---

## 📁 Estructura del Proyecto

```
analisis/
│
├── main.py                      # Punto de entrada de la aplicación
├── config.py                    # Configuración global y parámetros
├── user_config.json             # Configuración persistente del usuario
│
├── models/                      # Lógica de negocio y procesamiento
│   ├── waveform_data.py        # Gestión de archivos y datos de waveforms
│   ├── peak_analyzer.py        # Algoritmo principal de análisis
│   ├── analysis_results.py     # Estructura de resultados
│   ├── signal_processing.py    # FFT y procesamiento de señal
│   ├── signal_filters.py       # Filtros digitales (Savitzky-Golay, etc.)
│   ├── pulse_analysis.py       # Análisis de forma de pulso
│   ├── results_cache.py        # Sistema de caché de resultados
│   ├── favorites_manager.py    # Gestión de favoritos
│   └── baseline_tracker.py     # Seguimiento histórico de baseline
│
├── views/                       # Interfaz gráfica de usuario
│   ├── main_window.py          # Ventana principal
│   ├── control_sidebar.py      # Panel de controles y parámetros
│   ├── plot_panel.py           # Panel de visualización de waveforms
│   ├── peak_info_panel.py      # Panel de información estadística
│   └── popups/                 # Ventanas emergentes
│       ├── temporal_distribution_window.py
│       ├── signal_processing_window.py
│       ├── charge_histogram_window.py
│       ├── all_waveforms_window.py
│       └── tabbed_comparison_window.py
│
├── controllers/                 # Controladores MVC
│   ├── app_controller.py       # Controlador principal
│   ├── analysis_controller.py  # Controlador de análisis
│   └── comparison_controller.py # Controlador de comparación
│
└── utils/                       # Utilidades y helpers
    ├── plotting.py             # Funciones de visualización
    ├── file_utils.py           # Operaciones de archivos
    └── export.py               # Exportación de resultados
```

### Arquitectura MVC

El proyecto sigue el patrón **Model-View-Controller**:

- **Models** (`models/`): Lógica de procesamiento de datos, algoritmos de análisis
- **Views** (`views/`): Interfaz gráfica, visualización, interacción con usuario
- **Controllers** (`controllers/`): Coordinación entre modelos y vistas

---

## 📖 Guía de Uso

### 1. Cargar Datos

Al iniciar la aplicación:
1. Click en **"Cambiar Carpeta"** para seleccionar el directorio con datos
2. El directorio debe contener:
   - Archivos de waveform: `<nombre_dataset>_XXXX.txt`
   - Archivo de metadatos: `DATA.txt` (opcional)

### 2. Configurar Parámetros de Análisis

**Panel de Controles** (izquierda):

- **Prominence (%)**: Altura mínima relativa de picos (0.1-5%)
  - Valores bajos: Detecta picos pequeños (más sensible, más ruido)
  - Valores altos: Solo picos prominentes (menos sensible, más limpio)

- **Width (µs)**: Ancho mínimo de pico en microsegundos
  - Filtra pulsos muy estrechos (ruido electrónico)

- **Min Distance (µs)**: Distancia mínima entre picos
  - Evita detecciones múltiples del mismo pulso

- **Baseline (%)**: Rango percentil para definir línea base
  - Típicamente 85-95% para señales de SiPM

- **Max Dist (%)**: Zona temporal donde se espera el pico principal
  - Define la ventana de tiempo válida para el pulso

- **Afterpulse (%)**: Zona temporal para detectar afterpulsing
  - Identifica pulsos secundarios retardados

### 3. Ejecutar Análisis

1. Click en **"Actualizar"** para iniciar el análisis
2. La UI permanece responsiva (análisis en background)
3. Barra de progreso muestra el estado
4. Resultados aparecen automáticamente al finalizar

### 4. Explorar Resultados

**Navegación**:
- Usa flechas ◀ ▶ para navegar entre waveforms
- Cada panel muestra una categoría diferente
- El contador muestra posición actual (ej: "1/1234")

**Información Estadística** (panel derecho):
- Total de waveforms analizados
- Distribución por categorías
- Picos detectados
- Amplitud de baseline

**Favoritos**:
- Click derecho en un plot → "Añadir a Favoritos"
- Accede a favoritos desde el panel dedicado
- Los favoritos se guardan persistentemente

### 5. Análisis Avanzado

**Distribución Temporal**:
- Visualiza frecuencia vs amplitud de todos los picos
- Identifica patrones en la distribución de señales

**Procesamiento de Señal**:
- FFT para análisis de frecuencias
- Filtros digitales (Savitzky-Golay, pasa-bajos)
- Análisis de ruido y SNR

**Waveform Completa**:
- Superposición de todas las señales
- Modos: Superposición (tiempo local) y Distribuido (tiempo global)
- Filtros por categoría y muestreo configurable

**Comparación de Datasets**:
- Compara dos conjuntos de datos lado a lado
- Múltiples pestañas: Visualización, Amplitudes, Temporal, Carga, Waveforms

---

## 🏗️ Arquitectura del Software

### Flujo de Datos

```
┌─────────────────┐
│  Archivos .txt  │
│  (Osciloscopio) │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  WaveformData       │  ← Carga y parseo de archivos
│  - load_files()     │  ← Calcula estadísticas básicas
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  PeakAnalyzer       │  ← Análisis principal
│  - analyze_all()    │  ← Detección de picos
│  - classify()       │  ← Clasificación
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  AnalysisResults    │  ← Resultados estructurados
│  - accepted         │
│  - rejected         │
│  - afterpulse       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  ResultsCache       │  ← Caché para reutilización
│  - save/load        │
└─────────────────────┘
```

### Componentes Clave

#### 1. WaveformData (`models/waveform_data.py`)
- **Responsabilidad**: Gestión de archivos y datos crudos
- **Funciones principales**:
  - `load_files()`: Carga lista de archivos y calcula estadísticas ligeras
  - `read_waveform_file()`: Lee y parsea archivos individuales
  - Almacena: `global_min_amp`, `global_max_amp`, `all_max_times`

#### 2. PeakAnalyzer (`models/peak_analyzer.py`)
- **Responsabilidad**: Algoritmo de análisis y clasificación
- **Funciones principales**:
  - `analyze_all()`: Orquesta el análisis completo
  - `_analyze_waveforms_parallel()`: Procesamiento paralelo
  - `_filter_by_baseline()`: Filtra picos por baseline
  - `_find_main_candidates()`: Identifica picos principales
  - `_classify_waveform()`: Clasifica en accepted/rejected/afterpulse

#### 3. AnalysisResults (`models/analysis_results.py`)
- **Responsabilidad**: Estructura de datos de resultados
- **Atributos**:
  - `accepted_results`: Lista de WaveformResult aceptados
  - `rejected_results`: Lista de WaveformResult rechazados
  - `afterpulse_results`: Lista de WaveformResult con afterpulse
  - `favorites_results`: Lista de favoritos del usuario
  - Thresholds: `baseline_low/high`, `max_dist_low/high`, `afterpulse_low/high`

#### 4. ResultsCache (`models/results_cache.py`)
- **Responsabilidad**: Persistencia de resultados
- **Funcionalidad**:
  - Genera hash único basado en archivos y parámetros
  - Guarda/carga resultados en `.cache/`
  - Evita re-análisis de datos idénticos

---

## 🔍 Algoritmo de Análisis

### Pipeline de Análisis

```
1. CARGA DE DATOS
   ├─ Listar archivos en directorio
   ├─ Calcular estadísticas globales (min/max amplitud, tiempos)
   └─ Preparar para análisis

2. DETECCIÓN DE PICOS (por waveform)
   ├─ scipy.signal.find_peaks()
   │  ├─ prominence: altura relativa mínima
   │  ├─ width: ancho mínimo en samples
   │  └─ distance: distancia mínima entre picos
   └─ Resultado: Lista de índices de picos detectados

3. CÁLCULO DE THRESHOLDS GLOBALES
   ├─ Baseline: Percentil de todas las amplitudes
   ├─ Max Distance: Percentil de tiempos de máximo
   └─ Afterpulse: Percentil de tiempos de pulsos secundarios

4. FILTRADO Y CLASIFICACIÓN
   ├─ Filtrar picos por baseline (eliminar ruido)
   ├─ Identificar picos en zona de máximos
   └─ Clasificar:
      ├─ Accepted: 1 pico válido
      ├─ Afterpulse: >1 pico válido
      └─ Rejected: 0 picos válidos

5. POST-PROCESAMIENTO
   ├─ Calcular estadísticas por categoría
   ├─ Tracking de baseline histórico
   └─ Guardar en caché
```

### Criterios de Clasificación

**Accepted** (Señal limpia de 1 fotoelectrón):
- Exactamente 1 pico detectado
- Pico dentro de la zona de máximos (`max_dist_low` a `max_dist_high`)
- Amplitud por encima del baseline

**Afterpulse** (Señal con pulsos secundarios):
- Más de 1 pico detectado
- Al menos 1 pico en zona de máximos
- Pulsos adicionales fuera de la zona principal

**Rejected** (Señal no válida):
- 0 picos en zona de máximos
- Todos los picos filtrados por baseline
- Señal demasiado ruidosa o débil

---

## 📊 Formato de Datos

### Archivos de Waveform

Cada archivo `.txt` contiene una forma de onda capturada:

```
<t_half>                    # Línea 1: Tiempo central (trigger time)
<num_points>                # Línea 2: Número de puntos
<amplitude_1>               # Línea 3+: Amplitudes en voltios
<amplitude_2>
<amplitude_3>
...
<amplitude_N>
```

**Ejemplo**:
```
5.123456e-05
4081
-0.00234
-0.00231
-0.00229
...
```

### Archivo DATA.txt (Opcional)

Metadatos del experimento:

```
Time base scale: 5e-07 s/div
Trigger (0.5PE): 0.015 V
Num de puntos: 4081
Temperature: 77 K
SiPM Model: Hamamatsu S13360-3050CS
```

### Estructura de Directorios de Datos

```
SiPM4_LN2_DCR1/
├── DATA.txt                          # Metadatos
├── SiPM4_LN2_DCR1_0001.txt          # Waveform 1
├── SiPM4_LN2_DCR1_0002.txt          # Waveform 2
├── SiPM4_LN2_DCR1_0003.txt          # Waveform 3
└── ...
```

---

## ⚙️ Configuración

### config.py

Parámetros globales del sistema:

```python
# Parámetros de waveform (auto-detectados)
WINDOW_TIME = 5e-6          # Ventana temporal total (s)
TRIGGER_VOLTAGE = 0.0       # Voltaje de trigger (V)
NUM_POINTS = 4081           # Puntos por waveform
SAMPLE_TIME = 1.225e-9      # Tiempo entre muestras (s)

# Parámetros de análisis por defecto
DEFAULT_PROMINENCE_PCT = 2.0      # Prominence (%)
DEFAULT_WIDTH_TIME = 0.2e-6       # Ancho mínimo (s)
DEFAULT_MIN_DIST_TIME = 0.05e-6   # Distancia mínima (s)
DEFAULT_BASELINE_PCT = 85.0       # Baseline percentil
DEFAULT_MAX_DIST_PCT = 99.0       # Max dist percentil
DEFAULT_AFTERPULSE_PCT = 80.0     # Afterpulse percentil
```

### user_config.json

Configuración persistente del usuario:

```json
{
  "last_data_dir": "C:/path/to/data",
  "window_size": "1600x900",
  "theme": "Dark"
}
```

---

## 🤝 Contribuir

### Guía para Desarrolladores

1. **Fork** el repositorio
2. Crea una **rama** para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request**

### Estándares de Código

- **PEP 8**: Seguir guía de estilo de Python
- **Docstrings**: Documentar todas las funciones públicas
- **Type hints**: Usar anotaciones de tipo cuando sea posible
- **Comentarios**: Explicar lógica compleja

### Testing

Antes de hacer commit:
```bash
# Verificar que la aplicación inicia
python main.py

# Probar análisis con dataset pequeño
# Verificar que no hay errores en consola
```

---

## 📝 Notas Técnicas

### Optimizaciones Implementadas

1. **Threading de UI**: Análisis en background para mantener interfaz responsiva
2. **I/O Optimizado**: Lectura única de archivos con estadísticas en memoria
3. **Procesamiento Paralelo**: Uso de `ProcessPoolExecutor` para datasets grandes
4. **Caché de Resultados**: Evita re-análisis de datos idénticos
5. **Muestreo Adaptativo**: Visualización eficiente de miles de waveforms

### Limitaciones Conocidas

- **Memoria**: Datasets muy grandes (>50,000 waveforms) pueden requerir >8 GB RAM
- **Formato de Datos**: Solo soporta formato de texto plano del osciloscopio
- **Paralelización**: Limitada por número de cores del CPU

### Troubleshooting

**Problema**: La aplicación no inicia
- **Solución**: Verificar que todas las dependencias están instaladas

**Problema**: Análisis muy lento
- **Solución**: Verificar que el procesamiento paralelo está activo (>50 archivos)

**Problema**: Resultados inconsistentes
- **Solución**: Limpiar caché (`.cache/`) y re-analizar

---

## 📄 Licencia

Este proyecto es software académico desarrollado para investigación en física experimental.

## 👥 Autores

Desarrollado en el contexto de experimentos de caracterización de SiPMs para detectores de partículas.

## 📧 Contacto

Para preguntas o sugerencias sobre el software, contactar al equipo de desarrollo.

---

**Última actualización**: Diciembre 2024
