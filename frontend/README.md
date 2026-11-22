# Interfaz web de Fake Music Hunter

Aplicación de una sola página (SPA) en React + TypeScript, construida con Vite. Usa TanStack Query para las llamadas a la API y React Router para la navegación.

En producción no hace falta ningún servidor aparte: FastAPI sirve la carpeta `dist/` compilada (variable `FMH_STATIC_DIR`). Las rutas que no son `/api` devuelven `index.html`, así que las URLs internas como `/jobs/<id>` funcionan también al recargar la página.

## Estructura

```
src/
├── api/          # Tipos (alineados con src/web/schemas.py) y cliente HTTP
├── hooks/        # useHealth (detección de caídas) y useLiveJob (progreso SSE + polling)
├── components/   # Biblioteca, subida, resumen, tabla de resultados, avisos
├── pages/        # Nuevo análisis, trabajo (/jobs/:id) e historial (/jobs)
├── format.ts     # Textos en español y formato de números, fechas y tamaños
└── styles.css    # Tokens de diseño (claro/oscuro) y estilos
```

## Desarrollo con Docker

Todo se ejecuta en contenedores. `node_modules` vive en un volumen de Docker (`fmh-node-modules`), no en tu máquina. Comandos desde la raíz del repositorio:

```bash
# Instalar dependencias (solo la primera vez o al cambiar package.json)
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app \
  node:22-alpine npm install

# Compilar (comprueba tipos con tsc y genera frontend/dist)
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app \
  node:22-alpine npm run build

# Solo comprobar tipos
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app \
  node:22-alpine npm run typecheck
```

### Servidor de desarrollo con recarga en caliente

Vite reenvía las llamadas a `/api` al servidor FastAPI (variable `API_PROXY_TARGET`, por defecto `http://localhost:8000`). Con Docker, ambos contenedores comparten una red:

```bash
docker network create fmh-net

# 1. La API (con la imagen de desarrollo: docker build -f docker/dev.Dockerfile -t fmh-dev .)
docker run -d --name fmh-api --network fmh-net -v "$PWD":/app \
  -v "/ruta/a/tu/musica":/music:ro -e FMH_DATA_DIR=/tmp/fmh-data \
  fmh-dev uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port 8000

# 2. Vite, apuntando a la API
docker run --rm --name fmh-vite --network fmh-net -p 127.0.0.1:5173:5173 \
  -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app \
  -e API_PROXY_TARGET=http://fmh-api:8000 node:22-alpine npm run dev
```

Abre `http://localhost:5173`.

### Probar la versión compilada servida por FastAPI

```bash
docker run --rm -p 127.0.0.1:8000:8000 -v "$PWD":/app \
  -v "/ruta/a/tu/musica":/music:ro -e FMH_DATA_DIR=/tmp/fmh-data -e FMH_STATIC_DIR=/app/frontend/dist \
  fmh-dev uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port 8000
```

Abre `http://localhost:8000`.

## Notas

- Los tipos de `src/api/types.ts` se mantienen a mano: si cambias un modelo de la API, actualízalos.
- El progreso en vivo usa Server-Sent Events. Si la conexión SSE falla, la página consulta el estado cada 2 segundos.
- Las peticiones tienen un tiempo límite (5 s para `/api/health` y 15 s para el resto), para detectar un servidor que no responde y mostrar el aviso de conexión.
- Los colores de cada clasificación siempre van acompañados de su etiqueta de texto.
