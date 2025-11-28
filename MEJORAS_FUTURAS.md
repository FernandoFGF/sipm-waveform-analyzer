

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


