# Design

## Context

Hoy el código se reparte así:

- `src/main.py` orquesta en un bucle: `AudioScanner.scan()` → `AudioAnalyzer.analyze()` → `FakeDetector.detect()` → `Reporter`, con la barra de progreso de `rich`.
- `Reporter` mezcla dos funciones: acumula resultados e imprime en consola.
- `export_csv` modifica `result['bitrate']` al exportar (ver proposal.md, Why).
- `AudioAnalyzer` registra los errores con `print()`, devuelve dicts planos y carga 30 s de audio a 44,1 kHz mono. Cada archivo cuesta segundos de CPU (STFT con n_fft=4096), y librosa compila con numba en la primera llamada.
- Los módulos se importan como `from src.x import …`, así que el punto de entrada correcto es `python -m src.main`.
- Hay que seguir pudiendo construir el `.exe` con PyInstaller a partir de `src/main.py`.
- Las dependencias declaradas son librosa, numpy, scipy, mutagen, rich, click, pandas y soundfile. pandas no se usa.
- Los tests solo cubren `FakeDetector`.

Los requisitos están en `specs/` (audio-analysis-core, analysis-jobs, web-ui, container-runtime).

## Goals / Non-Goals

**Goals:**
- Un único servicio de análisis que usen la CLI, la API y los tests.
- Un solo contenedor y un solo proceso, sin servicios externos (ni Redis ni base de datos aparte), sencillo de desplegar en un NAS.
- La CLI y el build de Windows siguen funcionando sin arrastrar dependencias web.

**Non-Goals:**
- Autenticación de usuarios o multiusuario. Se documenta que el servicio debe exponerse solo en LAN o detrás de un proxy inverso con autenticación.
- Escalar horizontalmente con varias réplicas o workers de uvicorn.
- Cambiar umbrales o mejorar el algoritmo de detección.
- Visualizar espectrogramas en la web. Queda como mejora futura.
- Modificar, mover o borrar archivos de la biblioteca.

## Decisions

### 1. Servicio de análisis en `src/core/`
`src/core/service.py` expone `analyze_file(path) -> AnalysisResult` y `analyze_many(paths, on_progress, should_cancel) -> list[AnalysisResult]`. `AnalysisResult` es un `dataclass` con todos los campos de la spec; los que no se puedan calcular valen `None`. Tiene `to_dict()`.

`src/core/reports.py` contiene funciones puras `to_csv(results, fp)` y `to_json(results, fp)`, que trabajan sobre copias. `Reporter` queda solo como presentación de consola para la CLI y delega la exportación en `reports`. `AudioAnalyzer` y `FakeDetector` no cambian de interfaz; solo se sustituye `print` por `logging`.

- *Alternativa*: que la web reutilice `Reporter` directamente. Se descarta porque está acoplado a `rich.Console` y a estado mutable.

### 2. FastAPI + uvicorn, en `src/web/`
`src/web/app.py` (factory `create_app(settings)`; se arranca con `uvicorn src.web.app:create_app --factory`, para que importar el módulo no lea la configuración ni cree carpetas), `routes/`, `jobs.py`, `store.py` y `settings.py`. La configuración llega por variables de entorno con prefijo `FMH_` (pydantic-settings).

`src/main.py` no importa nada de `src/web`, así que PyInstaller sigue sin incluir FastAPI. Las dependencias web van en `requirements-web.txt`, que incluye `requirements.txt`.

- *Alternativas*: Flask, porque es síncrono y SSE resulta incómodo, y Django, que es excesivo para esto.

API (prefijo `/api`):

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health` | estado, versión, `library_available` |
| GET | `/library?path=<rel>` | subdirectorios + recuento de audio |
| POST | `/jobs` | JSON `{path, recursive, formats}` → trabajo de carpeta |
| POST | `/jobs/upload` | multipart `files[]` → trabajo de subida |
| GET | `/jobs` | historial (paginado) |
| GET | `/jobs/{id}` | estado, progreso, resumen |
| GET | `/jobs/{id}/results?classification=&format=&q=&offset=&limit=` | resultados |
| GET | `/jobs/{id}/events` | SSE de progreso |
| GET | `/jobs/{id}/report.csv` \| `/report.json` | descarga |
| POST | `/jobs/{id}/cancel` | cancelar |

El resto de rutas sirven la SPA: `StaticFiles` y, como fallback, `index.html` para cualquier ruta que no empiece por `/api`.

### 3. Ejecución con `ProcessPoolExecutor` y un `JobManager` en proceso
El análisis es CPU-bound y está limitado por el GIL, así que se usa un pool de procesos con `max_workers=FMH_WORKERS` (por defecto `min(2, os.cpu_count())`). El pool es compartido por todos los trabajos, lo que limita la concurrencia global como pide la spec.

`JobManager` es una tarea asyncio por trabajo. Envía los archivos al pool en una ventana acotada (≈ 2 × workers) en lugar de encolarlos todos. Así la cancelación detiene los archivos pendientes de inmediato y el progreso se emite archivo a archivo.

El worker llama a `core.service.analyze_file`. En el worker solo se pasan rutas y resultados serializables.

Como solo hay un proceso uvicorn (`--workers 1`), el estado de los trabajos en curso puede vivir en memoria, con el respaldo de SQLite.

- *Alternativas*: Celery/RQ + Redis añade un servicio más y no aporta nada a un único usuario. `BackgroundTasks` de FastAPI ejecuta en un thread, bloquea por el GIL y no permite cancelar.

### 4. Persistencia en SQLite (`/data/fmh.sqlite3`)
Se usa `sqlite3` de la stdlib con dos tablas:
- `jobs`: id (uuid), source (`library` \| `upload`), params JSON, status, total, processed, counts JSON, error, created_at y finished_at.
- `results`: job_id, idx, classification, format, file_name y data JSON, con índice por `(job_id, classification)`.

Los resultados se insertan según llegan, de modo que se pueden consultar mientras el trabajo corre y no se pierden si el servicio cae.

Al arrancar, los trabajos que estén en `queued` o `running` pasan a `failed` con la razón "interrumpido por reinicio". Una tarea periódica borra los trabajos cuya antigüedad supere `FMH_RETENTION_DAYS` y limpia `/data/uploads/` de restos huérfanos.

- *Alternativas*: guardar solo en memoria no cumple la persistencia que pide la spec. Usar archivos JSON por trabajo complica las consultas filtradas y paginadas.

### 5. Progreso por SSE con polling de respaldo
`GET /jobs/{id}/events` emite eventos `progress` (processed, total, counts y último resultado) y un evento `done` final. Se elige SSE porque la comunicación es unidireccional, lo soporta `EventSource` de forma nativa y atraviesa proxies sin configuración especial. Si `EventSource` falla, la SPA consulta `GET /jobs/{id}` cada 2 s.

- *Alternativa*: WebSocket, que es bidireccional sin necesitarlo y requiere más código y más configuración de proxy.

### 6. Seguridad de rutas y subidas
- **Rutas**: `safe_resolve(rel)` hace `(LIBRARY_ROOT / rel).resolve()` y exige `is_relative_to(LIBRARY_ROOT.resolve())`. Rechaza `..`, rutas absolutas y symlinks que salgan de la raíz. El escaneo también descarta cualquier archivo cuyo `resolve()` quede fuera de la raíz.
- **Subidas**:
  - Se hace streaming a `/data/uploads/<job_id>/` por bloques, contando bytes y abortando con 413 si se supera `FMH_MAX_UPLOAD_MB`; en ese caso se borran los parciales.
  - El nombre se sanea con `Path(name).name`, sin separadores, y se añade un prefijo índice para evitar colisiones.
  - Se valida la extensión contra `SUPPORTED_FORMATS`.
  - Al terminar, `shutil.rmtree` en un `finally`.
- En resultados de subida, `file_path` muestra el nombre original, no la ruta interna.

### 7. Frontend: React + TypeScript + Vite en `frontend/`
- TanStack Query para la caché y los reintentos de la API, y React Router para las vistas `/` (nuevo análisis: pestañas Biblioteca / Subir), `/jobs` (historial) y `/jobs/:id` (progreso + resultados).
- CSS propio con variables, para no añadir un framework de UI pesado. Los colores por clasificación coinciden con los de la CLI (verde, rojo, amarillo, gris), siempre acompañados de etiqueta textual.
- Tabla con ordenación y filtro en el cliente para la página cargada, y filtros de clasificación y formato en el servidor.
- Subida con `XMLHttpRequest` para poder mostrar el progreso, ya que `fetch` no informa del progreso de subida.
- Tipos de la API escritos a mano en `frontend/src/api/types.ts`, alineados con los modelos Pydantic. Generarlos desde OpenAPI queda como mejora.
- En desarrollo, `vite dev` con proxy `/api` → `localhost:8000`. En producción, `vite build` genera `frontend/dist`, que se copia a la imagen y se sirve desde FastAPI (`FMH_STATIC_DIR`).

- *Alternativas*: Vue sería equivalente, pero el usuario eligió el enfoque SPA y React tiene más ecosistema. Next.js añade SSR, que no hace falta, y obligaría a ejecutar Node en runtime.

### 8. Docker multi-stage
1. `node:22-alpine`: `npm ci && npm run build`.
2. `python:3.13-slim`:
   - `apt-get install ffmpeg libsndfile1` para decodificar MP3 con audioread y soundfile.
   - `pip install -r requirements-web.txt` y copia de `src/` y del `dist` del frontend.
   - Usuario `app` (UID 1000). El UID/GID se ajusta con `user:` en compose o con `--user`, sin `gosu`, para no arrancar como root.
   - `ENV NUMBA_CACHE_DIR=/tmp/numba` (numba no puede escribir caché en `site-packages`).
   - `EXPOSE 8000`, `VOLUME /data` y `HEALTHCHECK` con `python -c "urllib.request.urlopen('http://127.0.0.1:8000/api/health')"`, porque la imagen slim no trae curl.
3. `docker/entrypoint.sh`:
   - Sin argumentos o con `web`: `uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port $FMH_PORT --workers 1`.
   - Con `cli …`: `python -m src.main "$@"`.
   - Con cualquier otra cosa: `exec "$@"`.

Variables y valores por defecto: `FMH_LIBRARY_ROOT=/music`, `FMH_DATA_DIR=/data`, `FMH_PORT=8000`, `FMH_WORKERS=2`, `FMH_MAX_UPLOAD_MB=500` y `FMH_RETENTION_DAYS=30`.

`docker-compose.yml` monta `${MUSIC_DIR}:/music:ro` y `./data:/data`. `.dockerignore` excluye `venv`, `node_modules`, `.git`, `dist`, `build` y `output`. La imagen multi-arch se construye con `docker buildx build --platform linux/amd64,linux/arm64`.

### 9. Versión única
`src/__init__.__version__` pasa a ser la fuente de verdad (`2.1.0`). La usan la cabecera de la CLI, `/api/health` y la SPA, que la lee de health. Se elimina el literal "v2.0" de `reporter.py`.

### 10. Tests
- `tests/test_reports.py`: CSV seguido de JSON sin mutación.
- `tests/test_service.py`: archivos WAV sintéticos generados con numpy y soundfile en `tmp_path` (seno de banda completa → legítimo; ruido filtrado con paso bajo a 16 kHz → fake; archivo corrupto → error).
- `tests/web/` con `httpx`/`TestClient`: path traversal, validación de subidas, ciclo de vida de un trabajo, filtros, descarga, cancelación y limpieza. En estos tests el pool se sustituye por ejecución síncrona.
- Frontend: `npm run build` y `tsc --noEmit` en CI. Un test e2e queda fuera de este cambio.

## Risks / Trade-offs

- **[numba/llvmlite sin wheels para Python 3.13 en alguna arquitectura]** → Fijar `numba>=0.61` y `librosa>=0.10.2`, y verificar el build arm64 en CI. Si falla, usar `python:3.12-slim` en la imagen, ya que el código es compatible.
- **[Primera llamada lenta por la compilación JIT de numba en cada proceso del pool]** → Hacer un *warm-up* opcional en el inicializador del pool (analizar 1 s de silencio) y mantener la caché en `NUMBA_CACHE_DIR`.
- **[Consumo de RAM: cada proceso carga librosa (~200–300 MB)]** → `FMH_WORKERS=2` por defecto y documentar cómo ajustarlo en NAS con poca memoria.
- **[Sin autenticación]** → Enlazar por defecto en compose solo a `127.0.0.1:8000` y advertir en la documentación. Si se necesita, la autenticación iría en un cambio posterior.
- **[Imagen grande, más de 1 GB con ffmpeg y la pila científica]** → Usar `--no-install-recommends`, limpiar la caché de apt y pip, y no instalar dependencias de test. Es asumible para este caso de uso.
- **[Bibliotecas muy grandes, decenas de miles de archivos]** → Resultados en SQLite paginados, ventana acotada de envíos al pool y escaneo como generador. La tabla de la SPA pagina en el servidor.
- **[Estado en memoria + un único worker de uvicorn]** → Es una limitación aceptada (Non-Goals). Fijar `--workers 1` en el entrypoint.
- **[Divergencia entre la CLI y la web]** → Ambas usan `core.service` y `core.reports`. Los tests de regresión del detector protegen la clasificación.

## Migration Plan

1. Refactorizar el core y la CLI sin cambiar su comportamiento, con tests de regresión en verde. Comprobar que el build PyInstaller sigue funcionando.
2. Añadir la API y los jobs con sus tests.
3. Añadir el frontend.
4. Añadir Docker, compose y documentación.

Cada paso se puede mergear por separado. Para revertir, basta con volver a la versión anterior de la imagen; el volumen `/data` es desechable, porque solo contiene resultados regenerables.

## Open Questions

- ¿Publicar la imagen en GHCR desde GitHub Actions al crear un tag? No afecta al diseño; se puede decidir al final.
- ¿Valor por defecto de `FMH_MAX_UPLOAD_MB`? Se propone 500 MB por archivo y se ajustará tras probar con FLAC hi-res reales.
