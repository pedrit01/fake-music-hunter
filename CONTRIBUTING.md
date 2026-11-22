# 🚀 Guía para contribuir

Gracias por querer mejorar **Fake Music Hunter**. Esta guía explica cómo preparar el entorno, cómo está organizado el código y cómo proponer cambios.

## ⚡ Entorno de desarrollo

Todo se ejecuta en Docker: no hace falta instalar Python, Node ni ffmpeg en tu equipo. La imagen de desarrollo tiene las dependencias y el código se monta en `/app`, así que solo hay que reconstruirla cuando cambian los `requirements*.txt`.

```bash
git clone https://github.com/pedrit01/fake-music-hunter.git
cd fake-music-hunter
docker build -f docker/dev.Dockerfile -t fmh-dev .

# Tests
docker run --rm -v "$PWD":/app fmh-dev pytest

# CLI contra tu música (siempre en solo lectura)
docker run --rm -v "$PWD":/app -v "/ruta/a/tu/musica":/music:ro fmh-dev python -m src.main -p /music -v

# API + interfaz compilada (http://localhost:8000)
docker run --rm -p 127.0.0.1:8000:8000 -v "$PWD":/app -v "/ruta/a/tu/musica":/music:ro \
  -e FMH_DATA_DIR=/tmp/fmh-data -e FMH_STATIC_DIR=/app/frontend/dist \
  fmh-dev uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port 8000
```

La interfaz se compila en un contenedor de Node; `node_modules` vive en un volumen de Docker, nunca en tu equipo:

```bash
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app node:22-alpine npm install
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app node:22-alpine npm run build
```

Para desarrollar la interfaz con recarga en caliente, ver [frontend/README.md](frontend/README.md).

Ejecuta la CLI siempre como módulo (`python -m src.main`) desde la raíz del repositorio: los módulos se importan como `from src.x import ...` y `python src/main.py` falla.

## 🔍 Organización del código

```
src/
├── main.py        → CLI
├── core/          → Núcleo compartido por la CLI y la web
│   ├── service.py →   analyze_file / analyze_many (nunca lanzan excepciones)
│   ├── result.py  →   AnalysisResult
│   └── reports.py →   Exportadores CSV y JSON
├── analyzer.py    → Análisis espectral (STFT, presencia espectral, corte)
├── detector.py    → Reglas de clasificación por formato
├── scanner.py     → Búsqueda de archivos de audio
├── reporter.py    → Salida por consola (rich)
├── config.py      → Umbrales y constantes
└── web/           → API FastAPI: trabajos en segundo plano, SQLite, rutas seguras, subidas, limpieza
frontend/src/      → Interfaz React + TypeScript (api/, hooks/, components/, pages/)
tests/             → pytest; tests/web cubre la API con un analizador falso
```

### Flujo de un análisis

```
CLI:  Scanner ─┐
               ├→ core.analyze_file → Analyzer (STFT) → Detector → AnalysisResult ─┬→ Reporter (consola)
Web:  JobManager (pool de procesos) ┘                                              ├→ core.reports (CSV/JSON)
                                                                                   └→ SQLite → API → interfaz
```

- La CLI nunca importa `src/web`, para que el ejecutable de Windows no incluya FastAPI.
- `analyze_file` convierte cualquier fallo en un resultado con clasificación `error`, así que un archivo dañado no detiene un análisis.
- Las rutas que crean trabajos deben ser `async def`, porque el gestor crea una tarea asyncio en el bucle en marcha.

## 🔧 Modificar el algoritmo

- **Umbrales de MP3**: `CUTOFF_THRESHOLDS` y `SUSPICIOUS_THRESHOLD` en `src/config.py`.
- **Umbrales de FLAC/WAV**: están escritos directamente en el código, no en `config.py`:
  - en `analyzer.calculate_spectral_stats`: −70 dB y −65 dB por bin, y las bandas de 18, 20 y 22 kHz;
  - en `detector.detect_flac`: 30, 15 y 5 % de presencia, −60 dB de energía y el corte de 16 500 Hz.
- **Duración analizada**: `ANALYSIS_DURATION` en `config.py` (30 segundos).

Después de cambiar el algoritmo, pasa los tests y compara la clasificación de una carpeta de prueba antes y después (`-j antes.json` / `-j despues.json`). Para comprobar casos concretos, mira su espectrograma en [Spek](https://www.spek.cc/), como explica [TESTING.md](TESTING.md).

### Añadir una métrica

1. Calcúlala y devuélvela en `analyzer.calculate_spectral_stats`.
2. Léela con `.get()` y un valor por defecto en `detector`.
3. Añade el campo a `AnalysisResult` (`core/result.py`) y rellénalo en `core/service.analyze_file`.
4. Muéstrala en `reporter.py` y, si debe ir en el CSV, añádela a `CSV_FIELDS` en `core/reports.py`.
5. Para verla en la web, añádela al tipo `AnalysisResult` de `frontend/src/api/types.ts`, que replica el modelo a mano, y al detalle de `ResultsTable.tsx`.

## 🧪 Tests

```bash
docker run --rm -v "$PWD":/app fmh-dev pytest                                   # todos
docker run --rm -v "$PWD":/app fmh-dev pytest --cov=src --cov-report=term-missing
docker run --rm -v "$PWD":/app fmh-dev pytest tests/test_detector.py::TestFakeDetector::test_detect_flac_fake
```

- `test_detector.py` usa diccionarios de análisis escritos a mano.
- `test_service.py` genera WAV sintéticos en el momento (ruido completo → legítimo, ruido filtrado a 16 kHz → fake, bytes basura → error), así que no hay audio en el repositorio.
- `tests/web` crea la app con un analizador falso que clasifica por el nombre del archivo, de modo que los tests de la API son rápidos.

Todo cambio debe dejar los tests en verde y, si añade comportamiento, venir con tests nuevos.

## 📝 Proponer un cambio

1. Crea una rama desde `develop` (`git checkout -b feature/mi-mejora develop`).
2. Para cambios de comportamiento, planifícalos con [OpenSpec](https://github.com/Fission-AI/OpenSpec) en `openspec/changes/`. Las especificaciones vigentes están en `openspec/specs/`.
3. Escribe los mensajes de commit en inglés, empezando por una etiqueta entre corchetes: `[add]`, `[fix]`, `[update]`, `[refactor]`, `[docs]`, `[test]`, `[ci]` o `[chore]`. Por ejemplo: `[fix] Keep bitrate in bps when exporting JSON`.
4. El código, los comentarios, los docstrings y los textos de la interfaz van en español.
5. Abre un pull request contra `develop`.

Si un archivo se clasifica mal, abre un issue con la salida del programa (`-v`) y, si puedes, una captura de su espectrograma en Spek.

## 🌟 Ideas para contribuir

- Detección de upsampling (por ejemplo, 44,1 kHz convertido a 96 kHz).
- Exportar el espectrograma de cada archivo como imagen y mostrarlo en el detalle de la web.
- Soporte para más formatos (AAC/M4A, OGG, OPUS).
- Detección de artefactos específicos de cada códec.

¿Dudas? Abre un issue en GitHub. Happy coding! 🎵
