# analysis-jobs Specification

## Purpose

Gestionar por HTTP los trabajos de análisis de audio, ya sea sobre carpetas de la biblioteca montada o sobre archivos subidos: creación, ejecución en segundo plano, progreso, resultados, exportación, cancelación y limpieza.

## Requirements

### Requirement: Navegación de la biblioteca
La API SHALL listar los subdirectorios y el número de archivos de audio soportados de cualquier carpeta situada dentro de la raíz de biblioteca configurada.

#### Scenario: Listado de una carpeta
- **WHEN** un cliente solicita el contenido de una ruta relativa válida dentro de la biblioteca
- **THEN** recibe sus subdirectorios y el recuento de archivos `.mp3`, `.flac` y `.wav`

#### Scenario: Biblioteca no configurada
- **WHEN** no hay raíz de biblioteca configurada o no existe
- **THEN** la API responde que la navegación no está disponible, y la subida de archivos sigue funcionando

### Requirement: Confinamiento de rutas
Toda ruta que reciba la API MUST resolverse dentro de la raíz de biblioteca. Las rutas que la abandonen, por `..`, por ruta absoluta o por enlace simbólico, MUST rechazarse sin leer nada del sistema de archivos.

#### Scenario: Intento de path traversal
- **WHEN** un cliente envía la ruta `../../etc`
- **THEN** la API responde con error 400 y no crea ningún trabajo

### Requirement: Trabajo sobre carpeta de la biblioteca
La API SHALL crear un trabajo de análisis a partir de una carpeta de la biblioteca, con opciones de recursividad y filtro de formatos equivalentes a las de la CLI, y devolver de inmediato su identificador.

#### Scenario: Creación de trabajo de carpeta
- **WHEN** un cliente crea un trabajo sobre `Albums/2024` con recursividad y formato `flac`
- **THEN** recibe un identificador de trabajo en estado `queued` o `running` sin esperar a que el análisis termine

#### Scenario: Carpeta sin archivos de audio
- **WHEN** la carpeta indicada no contiene archivos soportados
- **THEN** el trabajo termina en estado `completed` con cero resultados

### Requirement: Trabajo sobre archivos subidos
La API SHALL aceptar en una sola petición la subida de uno o varios archivos `.mp3`, `.flac` o `.wav` y crear con ellos un trabajo de análisis.

#### Scenario: Subida válida
- **WHEN** un cliente sube tres archivos FLAC
- **THEN** se crea un trabajo con total 3 y se devuelve su identificador

#### Scenario: Extensión no soportada
- **WHEN** un cliente sube un archivo `.ogg`
- **THEN** la API lo rechaza con un error que indica los formatos admitidos

#### Scenario: Límite de tamaño excedido
- **WHEN** un archivo supera el tamaño máximo de subida configurado
- **THEN** la API rechaza la petición con error 413 y no conserva datos parciales

### Requirement: Ejecución en segundo plano
Los trabajos MUST ejecutarse fuera del ciclo de peticiones HTTP, con un número limitado y configurable de análisis concurrentes. Mientras se analiza, la API debe seguir respondiendo.

#### Scenario: API responsiva durante un análisis largo
- **WHEN** hay un trabajo analizando cientos de archivos
- **THEN** las consultas de estado y el healthcheck siguen respondiendo con normalidad

### Requirement: Estado y progreso del trabajo
La API SHALL exponer el estado de cada trabajo (`queued`, `running`, `completed`, `failed` o `cancelled`), los archivos procesados, el total, el recuento por clasificación y las marcas de tiempo de creación y fin. El cliente SHALL poder recibir actualizaciones de progreso en tiempo real.

#### Scenario: Consulta de progreso
- **WHEN** un cliente consulta un trabajo en ejecución
- **THEN** recibe el número de procesados, el total y el recuento parcial por clasificación

#### Scenario: Trabajo inexistente
- **WHEN** un cliente consulta un identificador desconocido
- **THEN** la API responde con 404

### Requirement: Consulta de resultados
La API SHALL devolver los resultados de un trabajo, completado o en curso, paginados y filtrables por clasificación y formato.

#### Scenario: Filtro por clasificación
- **WHEN** un cliente pide los resultados del trabajo filtrando por `fake`
- **THEN** solo recibe los resultados con esa clasificación

### Requirement: Descarga de reportes
La API SHALL permitir descargar los resultados de un trabajo como CSV o JSON, con el mismo contenido que generaría la CLI.

#### Scenario: Descarga CSV
- **WHEN** un cliente descarga el reporte CSV de un trabajo completado
- **THEN** recibe un archivo `text/csv` con una fila por resultado

### Requirement: Cancelación de trabajos
La API SHALL permitir cancelar un trabajo en `queued` o `running`. Los archivos que aún no se han procesado no se analizan, y los resultados ya obtenidos se conservan.

#### Scenario: Cancelación en curso
- **WHEN** un cliente cancela un trabajo con 10 de 100 archivos procesados
- **THEN** el trabajo pasa a `cancelled` y conserva al menos esos 10 resultados

### Requirement: Limpieza de subidas y retención
Los archivos subidos MUST eliminarse al terminar su trabajo, sea cual sea el estado final. Los trabajos y sus resultados SHALL conservarse durante un periodo de retención configurable y después eliminarse.

#### Scenario: Borrado tras completar
- **WHEN** un trabajo de subida termina en `completed`, `failed` o `cancelled`
- **THEN** sus archivos subidos ya no existen en disco

#### Scenario: Persistencia tras reinicio
- **WHEN** el servicio se reinicia dentro del periodo de retención
- **THEN** los trabajos terminados y sus resultados siguen consultables, y los que estaban en curso aparecen como `failed` con una razón de interrupción

### Requirement: Healthcheck y versión
La API SHALL ofrecer un endpoint de salud sin autenticación que indique si el servicio está operativo, su versión y si hay una biblioteca configurada.

#### Scenario: Servicio sano
- **WHEN** se consulta el endpoint de salud
- **THEN** responde 200 con el estado, la versión y la disponibilidad de la biblioteca
