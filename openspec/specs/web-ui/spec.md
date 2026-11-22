# web-ui Specification

## Purpose

Interfaz web de una sola página, en español, desde la que lanzar análisis sobre la biblioteca o sobre archivos subidos, seguir su progreso y explorar, filtrar y descargar los resultados sin usar la línea de comandos.

## Requirements

### Requirement: Servida por la propia aplicación
La interfaz web SHALL servirse desde el mismo servicio y puerto que la API, sin requerir un servidor adicional.

#### Scenario: Acceso a la raíz
- **WHEN** un usuario abre `http://<host>:<puerto>/` en el navegador
- **THEN** se carga la interfaz web, y las rutas internas de la SPA siguen funcionando al recargar la página

### Requirement: Lanzar análisis de la biblioteca
La interfaz SHALL permitir navegar por las carpetas de la biblioteca montada, elegir una y lanzar su análisis con las opciones de recursividad y formatos.

#### Scenario: Escaneo desde el navegador de carpetas
- **WHEN** el usuario navega a una carpeta, marca "recursivo" y "FLAC" y pulsa analizar
- **THEN** se crea el trabajo y la interfaz muestra su vista de progreso

#### Scenario: Sin biblioteca montada
- **WHEN** el servicio no tiene biblioteca configurada
- **THEN** la sección de biblioteca muestra un aviso explicativo y la subida de archivos sigue disponible

### Requirement: Subir archivos para analizar
La interfaz SHALL permitir seleccionar o arrastrar uno o varios archivos de audio, mostrar el progreso de la subida y crear el trabajo cuando esta termine.

#### Scenario: Arrastrar y soltar
- **WHEN** el usuario arrastra dos archivos MP3 a la zona de subida
- **THEN** ve el progreso de la subida y, al finalizar, la vista de progreso del análisis

#### Scenario: Archivo rechazado
- **WHEN** el usuario intenta subir un formato no soportado o un archivo demasiado grande
- **THEN** la interfaz muestra un mensaje de error claro y no lanza el trabajo con ese archivo

### Requirement: Progreso en vivo
Mientras un trabajo se ejecuta, la interfaz SHALL mostrar el progreso (procesados/total), el recuento parcial por clasificación y los resultados a medida que llegan, sin que el usuario tenga que recargar.

#### Scenario: Actualización automática
- **WHEN** el trabajo avanza de 5 a 6 archivos procesados
- **THEN** el contador y la tabla se actualizan solos en pocos segundos

#### Scenario: Cancelar desde la interfaz
- **WHEN** el usuario pulsa "Cancelar" en un trabajo en curso
- **THEN** el trabajo se muestra como cancelado y conserva los resultados parciales

### Requirement: Exploración de resultados
La interfaz SHALL mostrar los resultados en una tabla ordenable y filtrable por clasificación, formato y nombre. Cada clasificación SHALL distinguirse por color y por una etiqueta de texto, no solo por color.

#### Scenario: Filtrar fakes
- **WHEN** el usuario selecciona el filtro "Fake"
- **THEN** la tabla solo muestra archivos clasificados como fake y el recuento coincide con el del resumen

#### Scenario: Detalle de un archivo
- **WHEN** el usuario abre el detalle de un resultado
- **THEN** ve la razón y todas las métricas: bitrate, frecuencia de corte, presencia espectral, energía en altas frecuencias, contenido >20 kHz y rango dinámico

### Requirement: Resumen y descarga
La interfaz SHALL mostrar un resumen con totales y porcentajes por clasificación y ofrecer la descarga del reporte en CSV y JSON.

#### Scenario: Descargar reporte
- **WHEN** el usuario pulsa "Descargar CSV" en un trabajo terminado
- **THEN** el navegador descarga el reporte CSV de ese trabajo

### Requirement: Historial de trabajos
La interfaz SHALL listar los trabajos recientes con su estado, origen (carpeta o subida), fecha y resumen, y permitir abrir cualquiera de ellos.

#### Scenario: Volver a un trabajo anterior
- **WHEN** el usuario abre un trabajo terminado desde el historial
- **THEN** ve su resumen y sus resultados

### Requirement: Usabilidad básica
La interfaz MUST usarse con normalidad en escritorio y en móvil (desde 360 px de ancho), estar en español y mostrar mensajes comprensibles cuando la API no responde o devuelve un error.

#### Scenario: API caída
- **WHEN** la API deja de responder mientras el usuario ve un trabajo
- **THEN** la interfaz muestra un aviso de conexión y reintenta sin perder los datos ya mostrados
