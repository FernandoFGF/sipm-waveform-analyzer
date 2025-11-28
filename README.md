# Peak Finder GUI - SiPM Waveform Analyzer

Aplicación GUI profesional para análisis de waveforms de SiPM (Silicon Photomultiplier) con detección automática de picos, clasificación de afterpulses y visualización avanzada.

## 🚀 Características

- **Detección automática de picos** con parámetros configurables
- **Clasificación inteligente** de señales:
  - Aceptados (1 pico válido)
  - Rechazados (0 picos)
  - Afterpulses (>1 picos)
  - Rechazados con afterpulses
- **Visualización en tiempo real** de todas las categorías
- **Análisis temporal global** con distribución de picos
- **Mapa de densidad** de todas las waveforms superpuestas
- **Interfaz moderna** con CustomTkinter (modo oscuro)
- **Controles interactivos** de zoom y navegación

## 📦 Requisitos

```bash
pip install customtkinter numpy matplotlib scipy
```

## 🎯 Uso

1. Coloca tus archivos de datos en el directorio especificado en `config.py` (`DATA_DIR`)
2. Ejecuta la aplicación:
   ```bash
   python main.py
   ```
3. Ajusta los parámetros según tus necesidades:
   - **Prominencia**: Sensibilidad de detección de picos
   - **Anchura Mínima**: Filtro por ancho de pico
   - **Baseline**: Rango de amplitud base

## 🔧 Configuración

Edita `config.py` para ajustar a tus datos:
- `DATA_DIR`: Directorio con los archivos de waveform
- `WINDOW_TIME`: Duración de la ventana de adquisición
- `NUM_POINTS`: Número de puntos por waveform
- Valores por defecto de parámetros de análisis

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
