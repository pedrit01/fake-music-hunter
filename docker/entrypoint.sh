#!/bin/sh
# Punto de entrada del contenedor.
#
#   web (por defecto)  → servidor web con la API y la interfaz
#   cli <opciones>     → CLI de análisis, p. ej.: cli -p /music -o /data/r.csv
#   cualquier otra cosa → se ejecuta tal cual (p. ej. sh)
set -e

mode="${1:-web}"

case "$mode" in
  web)
    # Un único worker: el estado de los trabajos en curso vive en memoria.
    exec uvicorn src.web.app:create_app --factory \
      --host 0.0.0.0 --port "${FMH_PORT:-8000}" --workers 1
    ;;
  cli)
    shift
    exec python -m src.main "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
