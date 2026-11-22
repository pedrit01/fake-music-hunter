# Tasks

## 1. Núcleo de análisis reutilizable y CLI

- [ ] 1.1 Crear `src/core/` con `AnalysisResult` (dataclass con todos los campos de la spec, `None` en métricas no calculables, `to_dict()`) y verificar con un test unitario que `to_dict()` incluye todas las claves.
- [ ] 1.2 Implementar `core.service.analyze_file`, que encapsula `AudioAnalyzer` + `FakeDetector` y convierte las excepciones en un resultado `error`. Verificar con `tests/test_service.py`, que usa WAVs sintéticos en `tmp_path`: banda completa → `legitimate`, paso bajo a 16 kHz → `fake`, bytes corruptos → `error`.
- [ ] 1.3 Implementar `core.service.analyze_many(paths, on_progress, should_cancel)` y verificar con un test que emite N progresos crecientes, que un archivo corrupto no detiene el lote y que `should_cancel` deja de procesar los pendientes.
- [ ] 1.4 Crear `core.reports.to_csv/to_json` como funciones puras: bitrate en kbps en el CSV y numérico en el JSON, y CSV con presencia espectral incluida. Verificar con `tests/test_reports.py` que CSV seguido de JSON no muta los resultados.
- [ ] 1.5 Sustituir los `print()` de `src/analyzer.py` por `logging` y verificar que `grep -n "print(" src/analyzer.py` no devuelve nada.
- [ ] 1.6 Refactorizar `src/main.py` y `src/reporter.py` para que usen `core.service` y `core.reports`, manteniendo las opciones, la salida y los marcadores ASCII. Verificar que `python -m src.main -p <carpeta de prueba> -v -o r.csv -j r.json` produce la misma salida que antes y que `pytest` sigue en verde, incluidos los 4 tests del detector.
- [ ] 1.7 Unificar la versión en `src/__init__.__version__ = "2.1.0"` y usarla en la cabecera de la CLI. Verificar que `python -m src.main --help` y la cabecera muestran 2.1.0.
- [ ] 1.8 Quitar `pandas` de `requirements.txt` y añadir `requirements-dev.txt` (pytest, pytest-cov, httpx). Verificar que un venv limpio instala y pasa `pytest`.
- [ ] 1.9 Comprobar que `src/main.py` no importa nada de `src/web` (`python -c "import src.main, sys; assert 'fastapi' not in sys.modules"`) y anotar en BUILD_RELEASE.md que el build PyInstaller no cambia.
- [ ] 1.10 Actualizar el README y CLAUDE.md: cambiar `python src/main.py` por `python -m src.main` y describir la nueva capa `src/core/`. Verificar que los comandos documentados funcionan tal cual.

## 2. API web y trabajos de análisis

- [ ] 2.1 Crear `requirements-web.txt` (incluye `requirements.txt` + fastapi, uvicorn[standard], python-multipart, pydantic-settings) y `src/web/settings.py` con las variables `FMH_*` y sus valores por defecto. Verificar con un test que las variables de entorno sobrescriben los valores por defecto.
- [ ] 2.2 Implementar `src/web/store.py` sobre SQLite (tablas `jobs` y `results`, índices) con migración al arrancar y marcado de los trabajos en curso como `failed` tras un reinicio. Verificar con tests de store en `tmp_path`.
- [ ] 2.3 Implementar `safe_resolve` y el filtro de escaneo confinado a `FMH_LIBRARY_ROOT`. Verificar con tests que `..`, rutas absolutas y symlinks que salen de la raíz devuelven 400 o quedan excluidos.
- [ ] 2.4 Implementar `JobManager` con un `ProcessPoolExecutor` compartido (`FMH_WORKERS`), ventana acotada de envíos, inserción incremental de resultados, cancelación y estados `queued/running/completed/failed/cancelled`. Verificar con tests que usan un executor síncrono inyectado: ciclo completo, cancelación a mitad y concurrencia máxima respetada.
- [ ] 2.5 Crear `create_app()` con `GET /api/health` (estado, versión, `library_available`) y `GET /api/library`. Verificar con `TestClient` las respuestas con y sin biblioteca configurada.
- [ ] 2.6 Implementar `POST /api/jobs` (carpeta, recursive, formats) y `POST /api/jobs/upload`: streaming a `/data/uploads/<id>/`, validación de extensión, límite `FMH_MAX_UPLOAD_MB` con 413 y nombres saneados. Verificar con tests: subida válida, `.ogg` rechazado, archivo demasiado grande sin restos en disco y carpeta vacía que termina `completed` con 0 resultados.
- [ ] 2.7 Implementar `GET /api/jobs`, `GET /api/jobs/{id}` (404 si no existe), `GET /api/jobs/{id}/results` con filtros y paginación y `POST /api/jobs/{id}/cancel`. Verificar con tests de filtros por clasificación y formato y de cancelación que conserva los resultados parciales.
- [ ] 2.8 Implementar el SSE `GET /api/jobs/{id}/events` (eventos `progress` y `done`). Verificar con un test que lee el stream de un trabajo pequeño y recibe N progresos y un `done`.
- [ ] 2.9 Implementar la descarga `report.csv` y `report.json` con `core.reports` y los `Content-Type`/`Content-Disposition` correctos. Verificar con un test que su contenido coincide con el que exporta la CLI.
- [ ] 2.10 Implementar la limpieza: borrar las subidas en un `finally` al terminar el trabajo y una tarea periódica de retención (`FMH_RETENTION_DAYS`) y huérfanos. Verificar con tests que no quedan archivos tras `completed`, `failed` o `cancelled` y que la retención borra los trabajos antiguos.
- [ ] 2.11 Documentar en el README la sección "API" (endpoints, variables `FMH_*` y el arranque local con `uvicorn src.web.app:app`) y verificar que el comando arranca y `/docs` muestra OpenAPI.

## 3. Interfaz web (SPA)

- [ ] 3.1 Crear `frontend/` con Vite + React + TypeScript, React Router y TanStack Query, con proxy `/api` → `:8000` en dev. Verificar que `npm run dev` carga la app y `npm run build` y `tsc --noEmit` pasan.
- [ ] 3.2 Crear el cliente API tipado (`src/api/types.ts`, `client.ts`) y el layout base en español con tokens CSS y colores de clasificación con etiqueta textual. Verificar con `tsc --noEmit` y revisión visual en escritorio y a 360 px.
- [ ] 3.3 Implementar la vista "Nuevo análisis → Biblioteca": navegador de carpetas con migas de pan y recuentos, opciones recursivo/formatos y botón analizar que redirige a `/jobs/:id`, más un aviso cuando no hay biblioteca. Verificar manualmente con una biblioteca de prueba y con la API sin biblioteca.
- [ ] 3.4 Implementar la vista "Nuevo análisis → Subir": drag & drop y selector múltiple, validación previa de extensión y tamaño, barra de progreso con XHR y errores de la API visibles. Verificar subiendo archivos válidos, un `.ogg` y uno demasiado grande.
- [ ] 3.5 Implementar la vista de trabajo `/jobs/:id`: progreso en vivo por SSE con polling de respaldo, resumen por clasificación con porcentajes, botón cancelar y descargas CSV/JSON. Verificar con un trabajo real que el contador avanza sin recargar y que cancelar conserva los resultados parciales.
- [ ] 3.6 Implementar la tabla de resultados: filtros de clasificación y formato en servidor, búsqueda por nombre, ordenación, paginación y un panel de detalle con todas las métricas y la razón. Verificar que el recuento con filtro "Fake" coincide con el resumen.
- [ ] 3.7 Implementar el historial `/jobs` (estado, origen, fecha y resumen) y el aviso de conexión con reintento cuando la API cae. Verificar parando la API con la vista abierta.
- [ ] 3.8 Servir `frontend/dist` desde FastAPI (`FMH_STATIC_DIR`) con fallback SPA a `index.html` para las rutas que no son `/api`. Verificar con un test de `TestClient` que `/jobs/abc` devuelve el HTML y `/api/unknown` devuelve 404 JSON.
- [ ] 3.9 Documentar en `frontend/README.md` el desarrollo del frontend (dev, build, proxy) y verificar que los comandos funcionan tal cual.

## 4. Contenedor Docker

- [ ] 4.1 Crear un `Dockerfile` multi-stage: build en `node:22-alpine` y runtime en `python:3.13-slim` con `ffmpeg` y `libsndfile1`, usuario `app` (UID 1000), `NUMBA_CACHE_DIR`, `EXPOSE 8000`, `VOLUME /data` y `HEALTHCHECK`. Añadir también `.dockerignore`. Verificar que `docker build -t fake-music-hunter .` termina sin errores.
- [ ] 4.2 Crear `docker/entrypoint.sh` con los modos `web` (por defecto, uvicorn `--workers 1`), `cli …` y `exec "$@"`. Verificar que `docker run --rm -v <musica>:/music:ro -v ./out:/data fake-music-hunter cli -p /music -o /data/r.csv` genera `r.csv` y sale con código 0.
- [ ] 4.3 Verificar en el contenedor que un MP3, un FLAC y un WAV de prueba se analizan sin `error`, que el proceso no corre como UID 0 (`docker exec … id -u`) y que `docker ps` muestra `healthy`.
- [ ] 4.4 Crear `docker-compose.yml` de ejemplo: `${MUSIC_DIR}:/music:ro`, `./data:/data`, puerto `127.0.0.1:8000:8000`, variables `FMH_*` y `user:` comentado. Verificar con `docker compose up -d` que la web navega la biblioteca y que el historial sobrevive a `docker compose down && up`.
- [ ] 4.5 Verificar el build multi-arch con `docker buildx build --platform linux/amd64,linux/arm64 .`. Si numba o llvmlite fallan en 3.13, aplicar el fallback a `python:3.12-slim` documentado en design.md.
- [ ] 4.6 Documentar en el README la sección "Docker": run, compose, variables, volúmenes, permisos UID/GID, modo CLI, la advertencia de no exponer el servicio sin proxy con autenticación y el ajuste de `FMH_WORKERS` según la RAM. Verificar que los comandos documentados funcionan tal cual.

## 5. Integración y cierre

- [ ] 5.1 Prueba end-to-end con la imagen final: analizar una carpeta real de la biblioteca desde la web y comparar las clasificaciones con las de la CLI sobre la misma carpeta, que deben coincidir al 100 %.
- [ ] 5.2 (Opcional) Añadir un workflow de GitHub Actions con `pytest`, `npm run build` y `docker buildx build` para amd64/arm64, y verificar que pasa en un PR.
- [ ] 5.3 Actualizar el CHANGELOG (v2.1.0: Docker, web, refactor del core y corrección del export CSV) y verificar que `openspec validate add-docker-web-ui --strict` pasa.

## Workflow follow-up

- Archivar la change con `/openspec-archive-change` tras revisar y mergear.
- Decidir si se publica la imagen en GHCR al crear tags (Open Question de design.md).
