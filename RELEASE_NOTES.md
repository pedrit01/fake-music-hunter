## 🎵 Fake Music Hunter 2.1.0 - Docker e interfaz web

Esta versión añade una **interfaz web** y una **API** empaquetadas en una imagen Docker. La CLI sigue funcionando igual.

### 🚀 Cómo usarla

**Docker (interfaz web)**, con la imagen publicada en GitHub Container Registry para amd64 y arm64:

```bash
docker run -d --name fake-music-hunter -p 127.0.0.1:8000:8000 \
  -v "/ruta/a/tu/musica":/music:ro -v fmh-data:/data \
  ghcr.io/pedrit01/fake-music-hunter:2.1.0
```

Abre `http://localhost:8000`. Con `docker compose`, o para construir la imagen tú mismo, clona el repositorio en esta versión:

```bash
git clone --branch Version-2.1.0 https://github.com/pedrit01/fake-music-hunter.git
cd fake-music-hunter
MUSIC_DIR="/ruta/a/tu/musica" docker compose up -d
```

**CLI desde el código fuente:** sigue las instrucciones del [README](https://github.com/pedrit01/fake-music-hunter#instalación).

---

### 🚀 Nuevas Características

#### Interfaz Web
- 🌐 **Aplicación web** (React + TypeScript) servida por el propio servicio en `http://localhost:8000`
- 📁 **Análisis de la biblioteca**: navegador de carpetas con recuento por formato, opción recursiva y filtro de formatos
- ⬆️ **Subida de archivos**: arrastrar y soltar, validación de formato y tamaño antes de subir y barra de progreso
- ⏱️ **Progreso en tiempo real** (Server-Sent Events, con consulta periódica si la conexión falla) y cancelación conservando los resultados parciales
- 📊 **Resultados**: resumen por clasificación, tabla con filtros, búsqueda, ordenación, paginación y detalle de todas las métricas
- 💾 Descarga de reportes **CSV y JSON** con el mismo formato que la CLI
- 🕘 **Historial** de análisis, aviso de conexión perdida, modo claro/oscuro y diseño adaptado a móvil

#### Mejoras de la interfaz (revisión UI/UX)
- 🔝 **Problemas primero**: los resultados se ordenan por gravedad (Fake → Sospechoso → Error → Legítimo) y el filtro gana la opción **"Solo problemas"**
- ↕️ La ordenación por columnas se resuelve en el servidor, así que se aplica a todos los resultados y no solo a la página visible
- 🏷️ **Título de la pestaña** con el progreso del análisis en curso (`45 % · Analizando…`) y su estado al terminar
- ⌨️ **Accesibilidad**: detalle de cada resultado operable con teclado, formatos agrupados bajo "Formatos", zonas de toque de al menos 24 px, barras de progreso etiquetadas y respeto a "reducir movimiento"
- 📱 **Móvil**: cada resultado en una fila compacta con la frecuencia de corte; el motivo pasa al detalle desplegable
- ✨ **Pulido visual**: iconos SVG propios en lugar de emojis, cifras alineadas a la derecha y de ancho fijo, y tarjetas del resumen con 0 atenuadas

#### API HTTP (FastAPI)
- Trabajos de análisis en segundo plano sobre un pool de procesos, con concurrencia limitada (`FMH_WORKERS`)
- Persistencia en SQLite: el historial sobrevive a reinicios y los trabajos interrumpidos se marcan como fallidos
- Rutas confinadas a la biblioteca (`..`, rutas absolutas y enlaces simbólicos que salen de ella se rechazan)
- Limpieza automática de subidas y de trabajos antiguos (`FMH_RETENTION_DAYS`)
- Configuración con variables `FMH_*` y documentación OpenAPI en `/docs`
- `GET /api/jobs/{id}/results` admite varias clasificaciones a la vez (`classification=fake&classification=suspicious`) y ordenación en el servidor con `sort` (`severity`, `file_name`, `format`, `bitrate`, `cutoff_frequency`, `spectral_presence`) y `order` (`asc`/`desc`). Los valores no admitidos devuelven 422

#### Docker
- 🐳 **Imagen única** con web, API y CLI: build multi-stage, usuario sin privilegios (UID 1000) y healthcheck
- `docker-compose.yml` de ejemplo: música en solo lectura, historial en `./data` y puerto solo en `127.0.0.1`
- Modo CLI dentro del contenedor: `docker run … fake-music-hunter cli -p /music -o /data/reporte.csv`
- Imagen publicada en **GitHub Container Registry** (`ghcr.io/pedrit01/fake-music-hunter:2.1.0`) para **linux/amd64 y linux/arm64**; también se puede construir desde el repositorio
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

- 62 tests: servicio de análisis con audio sintético generado en el momento, exportadores y API web (rutas, subidas, ciclo de vida de trabajos, cancelación, limpieza, filtros y ordenación de resultados)
- Verificado con una biblioteca real de 82 archivos (MP3, FLAC y WAV): la web y la CLI coinciden al 100 %

### 📚 Documentación

- README: secciones de Docker (imagen de GHCR, descarga del repositorio, arranque y actualización) y API web
- Licencia MIT (`LICENSE`)
- `frontend/README.md`: desarrollo de la interfaz con Docker
- Workflow de GitHub Actions (tests, build web y build multi-arch), de momento con arranque manual
