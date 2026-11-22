# Proposal

## Why

Hoy Fake Music Hunter solo se puede usar como CLI. Hay que instalar a mano Python 3.13 y las dependencias de audio (librosa, numba, libsndfile/ffmpeg), o recurrir a un `.exe` de ~114 MB que solo funciona en Windows. Empaquetarlo en Docker con una interfaz web permitiría ejecutarlo igual en cualquier sistema, también en un NAS o servidor junto a la biblioteca musical. Además, los resultados (legítimo/fake/sospechoso y sus métricas) se podrían explorar de forma visual en lugar de leer la salida de consola.

La revisión del proyecto muestra que el código actual no está preparado para reutilizarse desde un servidor web:

- La orquestación del análisis vive dentro de `main()` en `src/main.py`, mezclada con la barra de progreso de `rich`.
- `Reporter` acumula estado y escribe directamente en consola.
- `AudioAnalyzer` informa de los errores con `print()`.
- `Reporter.export_csv` modifica los resultados en memoria: convierte `bitrate` en un string `"320 kbps"`, así que un export JSON posterior sale corrupto.
- No hay forma de restringir rutas, algo imprescindible si un servidor acepta rutas o ficheros de clientes.

## What Changes

- **Núcleo de análisis reutilizable**: extraer de `main.py` un servicio (`analyze_file` / `analyze_many`) que devuelva resultados estructurados y emita progreso mediante callback. Lo usarán la CLI y la web. Se reemplazan los `print()` por `logging`, se corrige la mutación de resultados en `export_csv` y se unifica la versión (`__version__` dice 1.0.0 y la app dice v2.0).
- **API HTTP (FastAPI)**: endpoints para crear trabajos de análisis de dos maneras: sobre una carpeta de la biblioteca montada en el contenedor o subiendo archivos desde el navegador. También para consultar el progreso, listar resultados con filtros y descargar los reportes CSV/JSON.
- **Trabajos en segundo plano**: el análisis es CPU-intensivo (STFT de 30 s por archivo), así que se ejecuta fuera del hilo de peticiones con un pool de procesos de tamaño configurable. El progreso se puede consultar en tiempo real.
- **Interfaz web SPA**: frontend en React + TypeScript (Vite) con estas vistas:
  - Navegar por la biblioteca montada y lanzar escaneos.
  - Arrastrar y soltar archivos para subirlos.
  - Seguir el progreso en vivo.
  - Tabla de resultados filtrable por clasificación y formato, con el detalle de métricas y la razón de cada archivo.
  - Resumen por clasificación y botones de descarga de reportes.
- **Contenedor Docker**: `Dockerfile` multi-stage (build del frontend con Node + runtime Python 3.13-slim con `ffmpeg`/`libsndfile`), usuario no root, `docker-compose.yml` de ejemplo con la biblioteca montada en solo lectura y un volumen para reportes/subidas, y healthcheck. La CLI sigue disponible dentro de la imagen (`docker run … cli -p /music`).
- **Seguridad básica**: las rutas de escaneo se limitan a la raíz de la biblioteca configurada (sin path traversal), se validan la extensión y el tamaño de las subidas, y los archivos subidos se borran tras el análisis o al expirar.
- Se mantiene la CLI actual con las mismas opciones y la misma salida. No se modifican los umbrales ni el algoritmo de detección.

## Capabilities

### New Capabilities
- `audio-analysis-core`: análisis de un archivo o un conjunto de archivos como servicio reutilizable, con resultados estructurados, informe de progreso y serialización de reportes CSV/JSON sin efectos secundarios.
- `analysis-jobs`: ciclo de vida de un trabajo de análisis iniciado por HTTP (sobre una carpeta de la biblioteca o sobre archivos subidos): creación, ejecución en segundo plano, progreso, resultados, cancelación, exportación y limpieza.
- `web-ui`: interfaz web de una sola página para lanzar análisis, seguir su progreso y explorar y descargar resultados.
- `container-runtime`: ejecución de la aplicación (web y CLI) en Docker, con su configuración por variables de entorno, volúmenes y healthcheck.

### Modified Capabilities
<!-- No existen specs previas en openspec/specs/. -->

## Impact

- **Código**: refactor de `src/main.py`, `src/reporter.py` y `src/analyzer.py`. Nuevos paquetes `src/core/` (servicio) y `src/web/` (FastAPI, jobs). Nuevo directorio `frontend/` (React/Vite).
- **Dependencias**: se añaden `fastapi`, `uvicorn[standard]` y `python-multipart`, más `httpx` y `pytest-cov` para tests. Se elimina `pandas`, que hoy no se usa. El frontend añade una toolchain Node solo en tiempo de build.
- **Infraestructura**: `Dockerfile`, `.dockerignore`, `docker-compose.yml`. Opcionalmente, un workflow de GitHub Actions para tests y build de la imagen.
- **Documentación**: README (sección Docker/web y corrección de `python src/main.py` → `python -m src.main`), CLAUDE.md y CHANGELOG.
- **Compatibilidad**: no hay cambios incompatibles en la CLI. El build PyInstaller para Windows debe seguir funcionando, y el punto de entrada `src/main.py` se mantiene.
