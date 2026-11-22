# container-runtime Specification

## Purpose

Ejecutar Fake Music Hunter, tanto la interfaz web como la CLI, dentro de un contenedor Docker autocontenido y configurable, apto para un PC, un servidor o un NAS junto a la biblioteca musical.

## Requirements

### Requirement: Imagen autocontenida
La imagen SHALL incluir todo lo necesario para decodificar y analizar MP3, FLAC y WAV, y para servir la interfaz web, sin requerir instalaciones en el host aparte de Docker.

#### Scenario: Análisis de los tres formatos
- **WHEN** se analiza dentro del contenedor un MP3, un FLAC y un WAV válidos
- **THEN** ninguno termina en `error` por falta de códecs o bibliotecas

### Requirement: Modo web por defecto
Al arrancar sin argumentos, el contenedor SHALL iniciar el servicio web escuchando en todas las interfaces, en el puerto configurado (8000 por defecto).

#### Scenario: Arranque por defecto
- **WHEN** se ejecuta `docker run -p 8000:8000 -v /ruta/musica:/music:ro <imagen>`
- **THEN** la interfaz web es accesible en `http://localhost:8000` y puede navegar `/music`

### Requirement: Modo CLI
El contenedor SHALL permitir ejecutar la CLI con sus mismas opciones en lugar del servicio web.

#### Scenario: Ejecución CLI en contenedor
- **WHEN** se ejecuta `docker run --rm -v /ruta/musica:/music:ro -v ./output:/data <imagen> cli -p /music -o /data/report.csv`
- **THEN** se imprime el análisis en consola, se genera `report.csv` en el volumen de salida y el contenedor termina con código 0

### Requirement: Configuración por variables de entorno
El contenedor SHALL configurarse mediante variables de entorno con valores por defecto documentados: raíz de la biblioteca, directorio de datos, puerto, número de análisis concurrentes, tamaño máximo de subida y días de retención de trabajos.

#### Scenario: Cambio de concurrencia
- **WHEN** se arranca con la variable de concurrencia igual a 4
- **THEN** el servicio analiza como máximo 4 archivos simultáneamente

### Requirement: Biblioteca en solo lectura
La aplicación MUST funcionar con la biblioteca montada en solo lectura y nunca escribir en ella. Reportes, subidas y estado se guardan solo en el directorio de datos.

#### Scenario: Volumen de música read-only
- **WHEN** la biblioteca se monta con `:ro`
- **THEN** los análisis de carpeta funcionan y no se produce ningún error de escritura

### Requirement: Persistencia de datos
El estado de trabajos, los resultados y los reportes SHALL guardarse en un directorio de datos montable como volumen, de modo que sobrevivan a la recreación del contenedor.

#### Scenario: Recrear contenedor
- **WHEN** se elimina y se vuelve a crear el contenedor con el mismo volumen de datos
- **THEN** los trabajos terminados siguen visibles en el historial

### Requirement: Ejecución sin privilegios
El proceso del contenedor MUST ejecutarse con un usuario no root, y SHALL poder ajustarse el UID/GID para que coincidan los permisos de los volúmenes.

#### Scenario: Usuario del proceso
- **WHEN** se inspecciona el proceso principal del contenedor en ejecución
- **THEN** no se ejecuta como UID 0

### Requirement: Healthcheck del contenedor
La imagen SHALL declarar un healthcheck basado en el endpoint de salud del servicio.

#### Scenario: Estado healthy
- **WHEN** el servicio web ha arrancado correctamente
- **THEN** `docker ps` muestra el contenedor como `healthy`

### Requirement: Composición de ejemplo
El proyecto SHALL incluir un archivo docker compose de ejemplo, con la biblioteca en solo lectura, un volumen de datos, el puerto publicado y las variables de entorno principales.

#### Scenario: Arranque con compose
- **WHEN** el usuario ajusta la ruta de su música en el compose y ejecuta `docker compose up -d`
- **THEN** la aplicación queda accesible en el puerto publicado y con la biblioteca navegable

### Requirement: Arquitecturas soportadas
La imagen SHALL poder construirse y ejecutarse en `linux/amd64` y `linux/arm64`.

#### Scenario: Ejecución en ARM
- **WHEN** se construye la imagen para `linux/arm64` y se ejecuta en un host ARM (por ejemplo, un Mac Apple Silicon o un NAS ARM)
- **THEN** arranca y analiza archivos igual que en amd64
