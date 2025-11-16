# 🚀 Guía Rápida para Desarrolladores

Bienvenido a **Fake Music Hunter**! Esta guía te ayudará a comenzar rápidamente.

## ⚡ Setup Rápido (5 minutos)

```bash
# 1. Clonar el repositorio
git clone https://github.com/pedrit01/fake-music-hunter.git
cd fake-music-hunter

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno (Windows)
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar tests
pytest -v

# 6. Probar la aplicación
python -m src.main --path "ruta/a/tus/audios" --formats flac --verbose
```

## 📚 Documentación Disponible

| Archivo | Descripción |
|---------|-------------|
| **[README.md](README.md)** | Descripción general, instalación y uso |
| **[ALGORITHM.md](ALGORITHM.md)** | Documentación técnica del algoritmo con diagramas |
| **[TESTING.md](TESTING.md)** | Guía completa de pruebas paso a paso |
| **[CHANGELOG.md](CHANGELOG.md)** | Historial de versiones y cambios |

## 🔍 Estructura Clave

```
src/
├── main.py       → CLI (punto de entrada)
├── analyzer.py   → Análisis espectral (aquí está la magia)
├── detector.py   → Algoritmo híbrido de clasificación
├── scanner.py    → Escaneo de archivos
├── reporter.py   → Generación de reportes
└── config.py     → Configuración y umbrales
```

## 🎯 Flujo de Datos

```
Archivo Audio → Scanner → Analyzer → Detector → Reporter
                   ↓          ↓          ↓          ↓
                 Path      STFT      Classify   Console/CSV/JSON
                         Metrics    (Hybrid)
```

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest -v

# Con cobertura
pytest --cov=src --cov-report=term-missing

# Solo un test específico
pytest tests/test_detector.py::TestFakeDetector::test_detect_flac_fake -v
```

## 🔧 Modificar el Algoritmo

### Ajustar Umbrales
Edita `src/config.py`:
```python
CUTOFF_THRESHOLDS = {
    'mp3_320': 20000,  # Ajusta aquí
    # ...
}
```

### Modificar Presencia Espectral
Edita `src/analyzer.py` → `calculate_spectral_stats()`:
```python
# Umbral de energía para bins
significant_high_freq = np.sum(spectrum_db[high_freq_mask] > -70)  # Ajusta -70
```

### Cambiar Clasificación
Edita `src/detector.py` → `detect_flac()`:
```python
if spectral_presence > 30:  # Ajusta 30
    return CLASS_LEGITIMATE, "..."
```

## 🐛 Debug Mode

Para ver información detallada durante el análisis:

```python
# En analyzer.py, descomenta:
print(f"Spectral presence: {spectral_presence:.1f}%")
print(f"Has content >20kHz: {has_content_above_20k}")
```

## 📊 Añadir Nueva Métrica

1. **Calcular en `analyzer.py`**:
```python
def calculate_spectral_stats(self):
    # ... código existente ...
    
    # Tu nueva métrica
    my_metric = calcular_algo(spectrum_db, frequencies)
    
    return {
        # ... existentes ...
        'my_metric': my_metric
    }
```

2. **Usar en `detector.py`**:
```python
def detect_flac(analysis_results):
    my_metric = analysis_results.get('my_metric', 0)
    
    if my_metric > threshold:
        return CLASS_LEGITIMATE, f"Mi métrica: {my_metric}"
```

3. **Mostrar en `reporter.py`**:
```python
def print_result(self, result):
    my_metric = result.get('my_metric')
    if my_metric:
        self.console.print(f"   • Mi métrica: {my_metric}")
```

## 🎨 Personalizar Salida

Colores y emojis en `src/config.py`:
```python
EMOJI_MAP = {
    CLASS_LEGITIMATE: '✅',  # Cambia aquí
    # ...
}

COLOR_MAP = {
    CLASS_LEGITIMATE: 'green',  # O 'blue', 'cyan', etc.
    # ...
}
```

## 🔬 Validar Cambios

Después de modificar el algoritmo:

```bash
# 1. Ejecutar tests
pytest -v

# 2. Probar con archivo conocido
python -m src.main --path "test_files/known_fake.flac" --verbose

# 3. Comparar resultados
# Antes: resultados_v1.json
# Después: resultados_v2.json
```

## 🚀 Tips de Desarrollo

1. **Usa pytest watch** para desarrollo continuo:
```bash
pip install pytest-watch
ptw
```

2. **Perfila el código** si es lento:
```bash
python -m cProfile -o profile.stats src/main.py --path "..."
```

3. **Visualiza con Spek** tus archivos de test para validar

4. **Git workflow**:
```bash
git checkout -b feature/mi-mejora
# hacer cambios
pytest -v  # asegurar que tests pasan
git commit -m "Añade mi mejora"
git push origin feature/mi-mejora
```

## ❓ FAQ Rápido

**P: ¿Cómo añado soporte para otro formato?**
R: Añade la extensión en `config.py` → `SUPPORTED_FORMATS` y crea un método `detect_xxx()` en `detector.py`

**P: ¿Cómo cambio el tiempo de análisis?**
R: Modifica `ANALYSIS_DURATION` en `config.py` (default: 30 segundos)

**P: ¿Por qué usa solo 30 segundos?**
R: Balance entre precisión y rendimiento. Puedes aumentarlo si necesitas más precisión.

**P: ¿Cómo exporto solo archivos fake?**
R: Filtra el CSV/JSON generado o modifica `reporter.py` para filtrar durante exportación

## 🌟 Mejoras Propuestas

Ideas para contribuir:
- [ ] Añadir GUI con Tkinter/PyQt
- [ ] Modo batch con multiprocessing
- [ ] Detección de upsampling
- [ ] Exportar espectrogramas como imágenes
- [ ] API REST para análisis remoto
- [ ] Integración con reproductores de música

## 📞 Contacto

¿Dudas? Abre un issue en GitHub o revisa la documentación completa.

Happy coding! 🎵
