# Design

## Context

- **Paginación de resultados.** `GET /api/jobs/{id}/results` pagina en el servidor y ordena siempre por `idx` (orden de llegada). La tabla (`ResultsTable`) ordena en el cliente solo la página cargada (50 filas), así que en trabajos con varias páginas el orden visible es engañoso.
- **Filtro por clasificación.** El filtro de clasificación es un único `str`, sin validar: un valor inexistente devuelve una lista vacía.
- **Almacenamiento.** La tabla `results` guarda `classification`, `format` y `file_name` como columnas, más el resultado completo en `data` (JSON). Hay índice por `(job_id, classification)`.
- **Frontend.** CSS propio con tokens en `styles.css`, sin librería de componentes ni de iconos. Los emojis 🎵 📁 ⬆️ hacen de iconos.
- **Restricciones del proyecto.** Todo se construye y prueba en Docker, el código debe ser legible y no se añaden dependencias sin necesidad.

## Goals / Non-Goals

**Goals:**
- Ordenación y filtro de problemas correctos sobre el conjunto completo de resultados, sin romper clientes existentes de la API.
- Cumplir lo básico de accesibilidad: teclado, etiquetas, zonas de toque de 24 px (WCAG 2.2 Target Size, mínimo) y movimiento reducido.
- Mantener el frontend sin dependencias nuevas.

**Non-Goals:**
- Rediseño visual, nueva paleta o tipografías externas. Se mantienen los tokens actuales y la fuente del sistema.
- Virtualización de la tabla o scroll infinito; la paginación de 50 filas se mantiene.
- Ordenar el historial de trabajos o cambiar el formato de los reportes CSV/JSON.
- Tests E2E dentro del repositorio. La verificación con Playwright sigue haciéndose desde el scratchpad.

## Decisions

### 1. Filtro por varias clasificaciones con parámetro repetido
`classification` pasa a ser `list[Literal["legitimate", "fake", "suspicious", "error"]]` en FastAPI: `?classification=fake&classification=suspicious`. En SQL se aplica como `classification IN (?, ?)`.

- **Compatibilidad:** con un solo valor el comportamiento es el de antes.
- **Valores desconocidos:** pasan a devolver 422 en lugar de una lista vacía. Lo consideramos una corrección, porque ningún cliente legítimo depende de ese caso.
- **Alternativa descartada:** un parámetro `problems=true`. Mezcla una regla de negocio en la API y no permite otras combinaciones.

### 2. Ordenación en el servidor con lista blanca
- **Parámetros nuevos:**
  - `sort: Literal["severity", "file_name", "format", "bitrate", "cutoff_frequency", "spectral_presence"] | None`
  - `order: Literal["asc", "desc"] = "asc"`
- **Sin `sort`:** se mantiene `ORDER BY idx`.
- **Construcción del `ORDER BY`:** `JobStore.list_results` traduce cada clave a una expresión SQL fija de un diccionario. El texto del cliente nunca llega a la consulta.
  - `severity` → `CASE classification WHEN 'fake' THEN 0 WHEN 'suspicious' THEN 1 WHEN 'error' THEN 2 ELSE 3 END`
  - `file_name` y `format` → columnas
  - métricas → `json_extract(data, '$.bitrate')`, etc.
- **Valores ausentes al final** en ambos sentidos, con `(<expr> IS NULL), <expr> <order>`.
- **Desempate estable:** `file_name, idx`, para que la paginación no repita ni salte filas.
- **Alternativa descartada:** añadir columnas para las métricas. Exige migración del esquema SQLite y duplicar datos, y `json_extract` es suficiente para el tamaño de un trabajo (miles a decenas de miles de filas filtradas por `job_id`).

### 3. Estado de filtros y orden en la tabla
- **Orden:** `ResultsTable` guarda `{ sort, order }`, con valor inicial `{ severity, asc }`, y lo incluye en la `queryKey`. Se elimina `sortRows` del cliente.
- **Cabeceras:** la de "Clasificación" ordena por `severity`. El resto usa su propia clave.
- **Filtro de clasificación:** pasa a ser una lista. El `select` gana la opción "Solo problemas" (`fake`, `suspicious`, `error`). Pulsar una tarjeta del resumen selecciona solo esa clasificación, como hasta ahora.
- **Alternativa descartada:** un checkbox "Solo problemas" aparte del `select`. Crea dos controles que pueden contradecirse (por ejemplo, "Legítimo" + "Solo problemas"). Con una sola opción en el `select` el estado es siempre coherente.

### 4. Título de la pestaña
- Un hook pequeño, `useDocumentTitle(title)`, fija `document.title` y lo restaura al desmontar. Lo usa cada página, con el formato `<página> · Fake Music Hunter`.
- `JobPage` calcula el título según el estado del trabajo:
  - en curso: `45 % · Analizando…`
  - terminado: `Completado`, `Cancelado` o `Fallido`
- El porcentaje se redondea a entero para no cambiar el título con cada archivo en trabajos grandes.

### 5. Fila de resultado operable con teclado
- El nombre del archivo pasa a ser un `<button>` con `aria-expanded` y `aria-controls`, que apunta a la fila de detalle.
- La fila conserva el clic con el ratón en toda su superficie. El botón detiene la propagación para no alternar el detalle dos veces.
- **Alternativa descartada:** `tabIndex` y `onKeyDown` sobre `<tr>`. Reimplementa lo que un botón nativo ya hace y los lectores de pantalla no anuncian bien su rol.

### 6. Móvil compacto
- Por debajo de 640 px:
  - El motivo (`.result-reason`) se oculta.
  - Se muestra un dato clave en la misma fila: la frecuencia de corte, que es la evidencia principal en los tres formatos.
- Es solo CSS, con clases `hide-mobile` y `mobile-only`. El detalle desplegable ya contiene el motivo y todas las métricas.

### 7. Iconos SVG propios
- Nuevo `components/Icon.tsx` con un puñado de iconos dibujados como SVG inline (`music`, `folder`, `arrow-up`, `x`).
- Usan `currentColor`, miden `1em` y llevan `aria-hidden="true"`, porque el texto contiguo ya da el significado.
- **Alternativa descartada:** `lucide-react`. Añade una dependencia para cuatro iconos.

### 8. Pulido CSS
- **Zonas de toque:**
  - `label.check` con `min-height: 24px` y padding.
  - Checkboxes de 18 px.
  - `.link-button` con padding vertical para llegar a 24 px.
- **Grupo de formatos:** `<fieldset>` con `<legend>Formatos</legend>`, sin borde por defecto.
- **Barras de progreso:** `aria-label` ("Progreso del análisis" y "Progreso de la subida").
- **Movimiento reducido:** `@media (prefers-reduced-motion: reduce)` anula `transition` y `animation`.
- **Cifras:** `td.number` y sus `th` alineados a la derecha, con `font-variant-numeric: tabular-nums`.
- **Tarjetas con 0:** clase `.summary-item.empty` con `background: var(--surface-muted)` y `color: var(--text-muted)`. No se usa opacidad, para mantener el contraste de 4,5:1 en claro y oscuro.
- **Navegador de carpetas:** si no hay subcarpetas y no hay carpeta padre, se muestra un texto discreto en lugar de la lista con borde.

## Risks / Trade-offs

- [Las filas cambian de posición durante un análisis en curso, porque los fakes nuevos suben arriba] → Es el comportamiento buscado. La invalidación ya está limitada a 1 por segundo, y el detalle abierto se identifica por `file_path`, así que no se pierde.
- [Coste de `json_extract` al ordenar por una métrica en trabajos muy grandes] → El filtro por `job_id` usa índice y el orden se calcula solo sobre ese trabajo. Si llegara a ser un problema, se añadirían columnas en un cambio posterior.
- [422 para clasificaciones desconocidas, donde antes salía una lista vacía] → Se documenta en el README. La SPA solo envía valores válidos.
- [El título dinámico puede molestar en pestañas fijadas] → Solo cambia en la vista de un trabajo en curso y con porcentajes enteros.

## Migration Plan

No hay migración de datos ni de esquema. Basta con desplegar la nueva imagen, y para volver atrás, la imagen anterior: la API sigue aceptando las peticiones antiguas.
