# Imagen de producción de Fake Music Hunter: interfaz web + API + CLI.
#
#   docker build -t fake-music-hunter .
#   docker run --rm -p 127.0.0.1:8000:8000 -v /ruta/musica:/music:ro -v ./data:/data fake-music-hunter
#
# Etapa 1: compila la interfaz web (solo se copia el resultado, dist/).
FROM node:22-alpine AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# Etapa 2: runtime de Python con la API, la CLI y la web compilada.
FROM python:3.13-slim

# Metadatos OCI: GHCR usa "source" para enlazar la imagen con el repositorio
LABEL org.opencontainers.image.title="Fake Music Hunter" \
      org.opencontainers.image.description="Detecta archivos de audio falsos o upscaleados mediante análisis espectral" \
      org.opencontainers.image.source="https://github.com/pedrit01/fake-music-hunter" \
      org.opencontainers.image.licenses="MIT"

# ffmpeg decodifica MP3 y libsndfile da soporte a FLAC/WAV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Solo las dependencias de ejecución (sin pytest ni httpx).
COPY requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

COPY src/ ./src/
COPY --from=frontend /frontend/dist/ ./static/
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# Usuario sin privilegios. /data debe existir y ser suyo para que el volumen
# con nombre herede los permisos; con bind mounts se ajusta con --user.
RUN useradd --uid 1000 --create-home app \
    && mkdir -p /data /music \
    && chown app:app /data \
    && chmod +x /usr/local/bin/entrypoint.sh

# numba (dependencia de librosa) necesita un directorio de caché escribible.
ENV NUMBA_CACHE_DIR=/tmp/numba \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FMH_LIBRARY_ROOT=/music \
    FMH_DATA_DIR=/data \
    FMH_STATIC_DIR=/app/static \
    FMH_PORT=8000

USER app
EXPOSE 8000
VOLUME /data

# La imagen slim no trae curl, así que la comprobación usa Python.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"FMH_PORT\", \"8000\")}/api/health', timeout=4)"

ENTRYPOINT ["entrypoint.sh"]
CMD ["web"]
