# Peak Finder GUI - SiPM Waveform Analyzer

Aplicación GUI profesional para# Analizador de Waveforms SiPM

Herramienta avanzada en Python y CustomTkinter para el análisis, visualización y comparación de señales de Fotomultiplicadores de Silicio (SiPM).

## 🚀 Características Principales

### 📊 Análisis de Waveforms
*   **Carga de Datos**: Soporta directorios con múltiples archivos de osciloscopio.
*   **Detección de Picos**: Algoritmos robustos para identificar picos de señal.
*   **Clasificación**: Separa automáticamente señales en Aceptadas, Rechazadas (pile-up/ruido) y Afterpulses.
*   **Visualización Interactiva**: Gráficos dinámicos con zoom, pan y selección de puntos.

### 🆚 Ventana de Comparación Avanzada (¡Nuevo!)
Sistema completo para comparar dos datasets lado a lado con múltiples herramientas:

1.  **Visualización**:
    *   Sub-pestañas para explorar por categoría: Aceptados, Rechazados, Afterpulses y Favoritos.
    *   Navegación waveform a waveform sincronizada.
2.  **Amplitudes**:
    *   Histogramas superpuestos de distribución de amplitudes de picos.
3.  **Temporal + FFT**:
    *   **Distribución Temporal**: Scatter plot logarítmico de diferencias temporales vs amplitud.
    *   **FFT**: Análisis de espectro de frecuencias comparativo.
4.  **Carga**:
    *   Histogramas de carga integrada (V·s) superpuestos.
5.  **Waveform Completa**:
    *   Visualización masiva de todas las señales.
    *   **Slider de Muestreo**: Control de densidad (10%, 25%, 50%, 75%, 100%).
    *   **Modos de Vista**:
        *   *Superposición*: Datasets lado a lado para comparación de forma.
        *   *Distribuida*: Visualización en tiempo global en plotes separados.

### ⚡ Rendimiento y Optimización (¡Nuevo!)
*   **Sistema de Caché Inteligente**: Almacena en memoria los resultados de datasets previamente comparados para una carga instantánea al reabrirlos.
*   **Muestreo Dinámico**: Ajuste automático de calidad gráfica según el volumen de datos.

## 🛠️ Instalación

1.  Clonar el repositorio:
    ```bash
    git clone https://github.com/FernandoFGF/sipm-waveform-analyzer.git
    ```
2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ Uso

Ejecutar el script principal:
```bash
python main.py
```
O usar el ejecutable `run.bat` en Windows.

## ⚙️ Configuración

El archivo `config.py` y `DATA.txt` permiten ajustar parámetros críticos como:
*   Ventana de tiempo y Sampling.
*   Umbrales de detección y voltaje de disparo.
*   Criterios de filtrado de ruido.

---
Desarrollado para análisis de laboratorio de física de partículas.
## 📝 Formato de Datos

Los archivos `.txt` deben tener el formato:
```
<tiempo_mitad_ventana>
<línea_vacía_o_header>
<amplitud_1>
<amplitud_2>
...
```

## 🎨 Capturas

<img width="1918" height="1025" alt="image (7)" src="https://github.com/user-attachments/assets/bf061448-76a2-4f33-a727-a64b9d5a6d25" />

## 📄 Licencia

MIT License

## 👤 Autor

Fernando
