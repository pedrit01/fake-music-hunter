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

### Requirement: Problemas primero
La tabla de resultados SHALL ordenarse por defecto por gravedad (Fake, Sospechoso, Error, Legítimo) y, dentro de cada clasificación, por nombre de archivo. Este orden SHALL aplicarse al conjunto completo de resultados del trabajo, no solo a la página visible.

#### Scenario: Fakes al principio en un trabajo grande
- **WHEN** el usuario abre un trabajo terminado con más resultados de los que caben en una página y algunos fakes llegaron al final del análisis
- **THEN** la primera página empieza por los resultados Fake, seguidos de los Sospechoso

### Requirement: Filtro de problemas
La interfaz SHALL ofrecer un control "Solo problemas" que muestre a la vez los resultados Fake, Sospechoso y Error. El recuento mostrado SHALL coincidir con la suma de esas clasificaciones en el resumen.

#### Scenario: Activar solo problemas
- **WHEN** el usuario activa "Solo problemas" en un trabajo con 3 Fake, 2 Sospechoso y 0 Error
- **THEN** la tabla muestra exactamente esos 5 resultados y el contador indica 5 archivos

#### Scenario: Combinar con otros filtros
- **WHEN** el usuario tiene activado "Solo problemas" y filtra además por formato MP3
- **THEN** la tabla solo muestra los problemas en formato MP3

### Requirement: Ordenación sobre todos los resultados
Al ordenar la tabla por una columna, la interfaz SHALL aplicar el orden al conjunto completo de resultados filtrados, de modo que la paginación respete ese orden. Los valores ausentes SHALL quedar al final en ambos sentidos.

#### Scenario: Ordenar por frecuencia de corte
- **WHEN** el usuario ordena por "Corte" de forma ascendente en un trabajo con varias páginas
- **THEN** la primera página contiene los cortes más bajos de todo el trabajo y la siguiente continúa a partir de ellos

### Requirement: Resultados operables con teclado
Cada resultado de la tabla SHALL poder desplegar y plegar su detalle con el teclado, y SHALL indicar a las tecnologías de apoyo si su detalle está abierto.

#### Scenario: Abrir el detalle con el teclado
- **WHEN** el usuario llega con Tab al nombre de un archivo y pulsa Enter o Espacio
- **THEN** se despliega el detalle de ese resultado con el foco visible, y una segunda pulsación lo pliega

### Requirement: Progreso en el título de la pestaña
El título del documento SHALL reflejar la página actual. En la vista de un trabajo en curso SHALL incluir el porcentaje de progreso, y al terminar SHALL indicar su estado final.

#### Scenario: Seguir un análisis desde otra pestaña
- **WHEN** un trabajo va por el 45 % y el usuario está en otra pestaña del navegador
- **THEN** el título de la pestaña de Fake Music Hunter muestra "45 %"

#### Scenario: Análisis terminado
- **WHEN** el trabajo termina
- **THEN** el título de la pestaña indica que está completado, cancelado o fallido

### Requirement: Resultados compactos en móvil
En pantallas de menos de 640 px, cada resultado SHALL mostrarse en una sola fila compacta con nombre, clasificación y un dato clave. El motivo de la clasificación SHALL quedar disponible en el detalle desplegable.

#### Scenario: Lista de resultados a 360 px
- **WHEN** el usuario ve un trabajo de 50 resultados en una pantalla de 360 px
- **THEN** cada resultado ocupa una fila sin el motivo debajo, sin scroll horizontal, y al abrir su detalle ve el motivo y todas las métricas

### Requirement: Zonas de toque suficientes
Todos los controles interactivos SHALL tener una zona de toque de al menos 24 × 24 px, incluidos checkboxes, enlaces de las migas de pan y el botón para quitar un archivo de la subida.

#### Scenario: Marcar un formato en móvil
- **WHEN** el usuario toca la etiqueta "FLAC" en una pantalla táctil
- **THEN** el checkbox cambia de estado, porque la zona de toque incluye la etiqueta y mide al menos 24 × 24 px

### Requirement: Controles agrupados y etiquetados
Los checkboxes de formatos SHALL presentarse como un grupo con una leyenda visible ("Formatos"). Cada barra de progreso SHALL tener una etiqueta accesible que describa qué progreso representa.

#### Scenario: Lector de pantalla en los formatos
- **WHEN** un lector de pantalla llega al checkbox "WAV"
- **THEN** anuncia que pertenece al grupo "Formatos"

### Requirement: Movimiento reducido
Cuando el sistema del usuario pida reducir el movimiento, la interfaz SHALL mostrar los cambios de estado sin animaciones ni transiciones.

#### Scenario: Preferencia de movimiento reducido
- **WHEN** el sistema operativo tiene activada la opción de reducir movimiento
- **THEN** la barra de progreso avanza sin animación

### Requirement: Iconos consistentes
Los iconos de la interfaz SHALL verse igual en todos los sistemas operativos y navegadores, sin depender de emojis. Los iconos decorativos SHALL ocultarse a las tecnologías de apoyo.

#### Scenario: Navegador de carpetas
- **WHEN** el usuario ve la lista de subcarpetas en Windows, macOS o Linux
- **THEN** cada carpeta muestra el mismo icono, y el lector de pantalla solo anuncia su nombre

### Requirement: Lectura de cifras y resumen
Las columnas numéricas de las tablas SHALL alinearse a la derecha con cifras de ancho fijo. Las tarjetas del resumen con recuento 0 SHALL mostrarse atenuadas, pero seguir siendo legibles y operables.

#### Scenario: Comparar bitrates
- **WHEN** el usuario recorre la columna "Bitrate"
- **THEN** las unidades, decenas y centenas de cada fila quedan alineadas verticalmente

#### Scenario: Clasificación sin resultados
- **WHEN** un trabajo no tiene ningún resultado con clasificación Error
- **THEN** la tarjeta "Error 0" aparece atenuada respecto a las que tienen resultados
