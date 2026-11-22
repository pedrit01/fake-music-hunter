# Imagen de desarrollo: ejecuta tests y la CLI sin instalar nada en el host.
#
#   docker build -f docker/dev.Dockerfile -t fmh-dev .
#   docker run --rm -v "$PWD":/app fmh-dev pytest
#
# El código se monta en /app, así que no hace falta reconstruir la imagen
# al editar código; solo al cambiar los requirements.
FROM python:3.13-slim

# ffmpeg decodifica MP3 y libsndfile da soporte a FLAC/WAV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# numba (dependencia de librosa) necesita un directorio de caché escribible.
ENV NUMBA_CACHE_DIR=/tmp/numba \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["pytest"]
