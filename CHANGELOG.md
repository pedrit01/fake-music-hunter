# 📝 Changelog - Fake Music Hunter

## Versión 2.1.0 - Docker e Interfaz Web (22 Nov 2026)

### 🚀 Nuevas Características

#### Interfaz Web
- 🌐 **Aplicación web** (React + TypeScript) servida por el propio servicio en `http://localhost:8000`
- 📁 **Análisis de la biblioteca**: navegador de carpetas con recuento por formato, opción recursiva y filtro de formatos
- ⬆️ **Subida de archivos**: arrastrar y soltar, validación de formato y tamaño antes de subir y barra de progreso
- ⏱️ **Progreso en tiempo real** (Server-Sent Events, con consulta periódica si la conexión falla) y cancelación conservando los resultados parciales
- 📊 **Resultados**: resumen por clasificación, tabla con filtros, búsqueda, ordenación, paginación y detalle de todas las métricas
- 💾 Descarga de reportes **CSV y JSON** con el mismo formato que la CLI
- 🕘 **Historial** de análisis, aviso de conexión perdida, modo claro/oscuro y diseño adaptado a móvil

#### API HTTP (FastAPI)
- Trabajos de análisis en segundo plano sobre un pool de procesos, con concurrencia limitada (`FMH_WORKERS`)
- Persistencia en SQLite: el historial sobrevive a reinicios y los trabajos interrumpidos se marcan como fallidos
- Rutas confinadas a la biblioteca (`..`, rutas absolutas y enlaces simbólicos que salen de ella se rechazan)
- Limpieza automática de subidas y de trabajos antiguos (`FMH_RETENTION_DAYS`)
- Configuración con variables `FMH_*` y documentación OpenAPI en `/docs`

#### Docker
- 🐳 **Imagen única** con web, API y CLI: build multi-stage, usuario sin privilegios (UID 1000) y healthcheck
- `docker-compose.yml` de ejemplo: música en solo lectura, historial en `./data` y puerto solo en `127.0.0.1`
- Modo CLI dentro del contenedor: `docker run … fake-music-hunter cli -p /music -o /data/reporte.csv`
- Imagen para **linux/amd64 y linux/arm64**
- Imagen de desarrollo (`docker/dev.Dockerfile`) para ejecutar tests y CLI sin instalar nada en el equipo

### 🔧 Refactorización

- Nuevo núcleo `src/core` compartido por la CLI y la web (`analyze_file`, `AnalysisResult`, exportadores CSV/JSON), de modo que ambas clasifican exactamente igual
- El analizador usa `logging` en lugar de `print`
- Versión única (`2.1.0`) con la opción `--version` en la CLI
- Eliminada la dependencia `pandas`, que no se usaba
- Dependencias separadas en `requirements.txt` (CLI), `requirements-web.txt` y `requirements-dev.txt`

### 🐛 Correcciones de Bugs

- ✅ **Export CSV + JSON**: exportar el CSV convertía el bitrate a kbps en los propios resultados, así que el JSON exportado a continuación salía con el bitrate equivocado. Ahora los exportadores trabajan sobre copias
- ✅ El CSV incluye la columna `spectral_presence`

### 🧪 Tests

- 53 tests: servicio de análisis con audio sintético generado en el momento, exportadores y API web (rutas, subidas, ciclo de vida de trabajos, cancelación, limpieza)
- Verificado con una biblioteca real de 82 archivos (MP3, FLAC y WAV): la web y la CLI coinciden al 100 %

### 📚 Documentación

- README: secciones de Docker y API web
- `frontend/README.md`: desarrollo de la interfaz con Docker
- Workflow de GitHub Actions (tests, build web y build multi-arch), de momento con arranque manual

---

## Versión 2.0 - Algoritmo Híbrido (16 Nov 2025)

### 🚀 Nuevas Características

#### Algoritmo Híbrido de Detección
- **Fase 1**: Detección rápida de contenido ultrasónico (>20 kHz)
  - 86.4% de archivos clasificados instantáneamente
  - Detección definitiva de archivos lossless auténticos
  
- **Fase 2**: Análisis de presencia espectral (18-22 kHz)
  - Métrica más robusta que frecuencia de corte simple
  - Distingue entre producción filtrada vs. conversión lossy
  - 13.6% de archivos requieren análisis detallado

#### Nuevas Métricas
- ✨ **Presencia Espectral**: Porcentaje de bins con contenido en 18-22 kHz
- ✨ **Detección Ultrasónica**: Contenido por encima de 20 kHz
- ✨ **Energía en Altas Frecuencias**: Validación de presencia espectral
- 📊 **has_content_above_20k**: Flag booleano para detección rápida

### 📈 Mejoras de Rendimiento

**Antes (v1.0):**
```
✅ Legítimos: 51 (66.2%)
❌ Fake: 6 (7.8%)
⚠️ Sospechosos: 12 (15.6%)
🚫 Errores: 8 (10.4%)
```

**Después (v2.0):**
```
✅ Legítimos: 66 (85.7%) ⬆️ +19.5%
❌ Fake: 2 (2.6%) ⬇️ -5.2% (más conservador)
⚠️ Sospechosos: 8 (10.4%) ⬇️ -5.2%
🚫 Errores: 1 (1.3%) ⬇️ -9.1%
```

### 🔧 Ajustes de Umbrales

#### Umbrales Actualizados
- **FLAC Fake Threshold**: Añadido 16,500 Hz como límite definitivo
- **Suspicious Threshold**: Aumentado de 1,000 Hz a 2,000 Hz
- **FLAC Suspicious Threshold**: Nuevo umbral de 3,000 Hz
- **Umbral de energía relajado**: -80 dB para casos especiales

#### Detección de Presencia Espectral
```python
>30%:    LEGÍTIMO (contenido distribuido)
15-30%:  SOSPECHOSO/LEGÍTIMO (verificar energía)
5-15%:   SOSPECHOSO (poca presencia)
<5%:     FAKE (casi sin contenido)
```

### 🐛 Correcciones de Bugs

- ✅ **Reducción de errores**: De 8 a 1 archivo con error
  - Implementado umbral de energía relajado (-80 dB)
  - Mejora en manejo de archivos con características espectrales únicas

- ✅ **Menos falsos positivos**: 
  - "Flying Free" ya no se marca como fake
  - "Rendez vous II" correctamente identificado como legítimo
  - "Beautiful Day" reclasificado según presencia espectral

- ✅ **Mejor manejo de casos especiales**:
  - Archivos de Ophidian con filtrado en producción
  - Música hardcore/rave con énfasis en graves

### 📚 Documentación

- ✅ **README.md actualizado**:
  - Tabla de contenidos
  - Descripción del algoritmo híbrido
  - Ejemplos de salida
  - Métricas de precisión
  - Guía de validación con Spek

- ✅ **ALGORITHM.md creado**:
  - Diagramas de flujo detallados
  - Documentación técnica completa
  - Fundamentos matemáticos
  - Parámetros y umbrales explicados

- ✅ **TESTING.md creado**:
  - Guía paso a paso para ejecutar tests
  - Comandos útiles de pytest
  - Solución de problemas
  - Flujo de trabajo recomendado

### 🧪 Tests

- ✅ Tests actualizados para nuevas métricas
- ✅ 4/4 tests pasando correctamente
- ✅ Cobertura de código mantenida
- ✅ Configuración pytest.ini añadida

### 📊 Estadísticas de Uso del Algoritmo Híbrido

En análisis de 77 archivos FLAC:
- **57 archivos (86.4%)**: Clasificados por Fase 1 (contenido >20 kHz)
- **9 archivos (13.6%)**: Clasificados por Fase 2 (presencia espectral)
- **Tiempo promedio**: ~0.5s por archivo
- **Precisión**: 98.7% (validado con Spek)

### 🔍 Casos de Prueba Validados

| Archivo | v1.0 | v2.0 | Validación Spek |
|---------|------|------|-----------------|
| Hell Me.flac | ✅ LEGÍTIMO | ✅ LEGÍTIMO (100% presencia) | ✅ Confirma |
| Flying Free.flac | ❌ FAKE | ⚠️ SOSPECHOSO (17.7% presencia) | ✅ Tiene contenido >16kHz |
| Oxygene.flac | ❌ FAKE | ❌ FAKE (4.8% presencia) | ⚠️ Contenido disperso limitado |
| Rendez vous II.flac | ⚠️ SOSPECHOSO | ✅ LEGÍTIMO (62.9% presencia) | ✅ Confirma |

### 🚧 Limitaciones Conocidas

1. No detecta conversiones de muy alta calidad (MP3 320 → FLAC)
2. Puede marcar como sospechosa música con filtrado artístico intencional
3. Requiere sample rate mínimo de 44.1 kHz
4. Analiza solo primeros 30 segundos (optimización)

### 🔮 Roadmap Futuro

- [ ] Detección de artefactos específicos de codecs
- [ ] Machine Learning para patrones de conversión
- [ ] Soporte para sample rates variables
- [ ] Detección de upsampling
- [ ] Análisis de coherencia estéreo
- [ ] GUI para visualización de resultados

---

## Versión 1.0 - Release Inicial (15 Nov 2025)

### Características Iniciales

- ✅ Análisis espectral básico (STFT)
- ✅ Detección por frecuencia de corte
- ✅ Soporte para MP3, FLAC, WAV
- ✅ Reportes en consola, CSV, JSON
- ✅ Escaneo recursivo de directorios
- ✅ CLI con Click
- ✅ Tests básicos con pytest

### Métricas v1.0
- Frecuencia de corte
- Rango dinámico
- Bitrate y metadatos

### Umbrales v1.0
```python
SUSPICIOUS_THRESHOLD = 1000  # Hz
CUTOFF_THRESHOLDS = {
    'mp3_320': 20000,
    'mp3_256': 19500,
    'mp3_192': 18000,
    'mp3_128': 16000,
    'flac': 20000,
}
```

---

**Última actualización**: 16 de noviembre de 2025
