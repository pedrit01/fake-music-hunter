# Proposal

## Why

En la revisión de UI/UX de la interfaz web (v2.1.0) aparecieron cuatro problemas:

- **Los problemas quedan escondidos.** En un análisis real de 82 archivos, los 3 "Fake" y los 2 "Sospechoso" quedan repartidos entre 77 legítimos ordenados por nombre. Con bibliotecas de miles de archivos se pierden entre páginas, porque la API pagina en orden de llegada y la ordenación actual solo afecta a la página cargada.
- **Accesibilidad.** Una parte de la interfaz no se puede usar con teclado: el detalle de un resultado solo se abre con el ratón.
- **Móvil.** La tabla de resultados ocupa unos 6.800 px de alto a 360 px de ancho.
- **Pulido visual.** Los emojis se usan como iconos y las cifras no están alineadas.

Conviene corregirlo ahora, antes de publicar la v2.1.0 en `main`, porque es la primera impresión de la interfaz.

## What Changes

**A. Problemas primero**
- Los resultados se ordenan por defecto por gravedad: Fake → Sospechoso → Error → Legítimo.
- Nuevo control "Solo problemas", que muestra Fake, Sospechoso y Error juntos.
- La ordenación por columnas pasa a resolverse en el servidor, así que se aplica a todos los resultados y no solo a la página visible.
- El título de la pestaña del navegador muestra el progreso de un análisis en curso y su estado al terminar. Cada página tiene un título propio.

**B. Accesibilidad**
- Las filas de resultados se pueden desplegar con el teclado (nombre del archivo como botón con `aria-expanded`).
- Los formatos del análisis de biblioteca se agrupan en un `fieldset` con leyenda "Formatos".
- Los controles pequeños tienen una zona de toque de al menos 24 × 24 px: checkboxes, "Quitar" y migas de pan.
- Las barras de progreso tienen etiqueta accesible.
- Se respeta `prefers-reduced-motion`.

**C. Móvil**
- Por debajo de 640 px, cada resultado ocupa una fila compacta con nombre, clasificación y un dato clave.
- El motivo se muestra solo en el detalle desplegable.

**D. Pulido visual**
- Iconos SVG propios en lugar de emojis.
- Columnas numéricas alineadas a la derecha y con cifras de ancho fijo.
- Las tarjetas del resumen con 0 se atenúan.
- El navegador de carpetas ya no muestra una caja vacía cuando no hay subcarpetas.

**API (retrocompatible)**
- `GET /api/jobs/{id}/results` acepta varias clasificaciones a la vez (`classification=fake&classification=suspicious`).
- El mismo endpoint acepta nuevos parámetros `sort` y `order`. Sin ellos, el comportamiento es el actual: orden de llegada.

## Capabilities

### New Capabilities
_Ninguna._

### Modified Capabilities
- `web-ui`: se añaden requisitos sin alterar los existentes:
  - Problemas primero, filtro de problemas y ordenación sobre todos los resultados.
  - Operación con teclado.
  - Progreso en el título de la pestaña.
  - Resultados compactos en móvil.
  - Zonas de toque, controles agrupados y movimiento reducido.
  - Iconos consistentes.
  - Lectura de cifras y resumen.
- `analysis-jobs`: "Consulta de resultados" añade el filtro por varias clasificaciones y la ordenación en el servidor.

## Impact

- **Frontend** (`frontend/src`):
  - Componentes: `ResultsTable`, `Summary`, `LibraryBrowser`, `UploadPanel` y `App`.
  - Páginas: `JobPage` y `HistoryPage`.
  - Resto: `api/client.ts`, `api/types.ts`, `styles.css` y un nuevo componente de iconos SVG. No se añaden dependencias.
- **Backend**:
  - `src/web/routes/jobs.py`: parámetros `classification` (lista), `sort` y `order`.
  - `src/web/store.py`: `list_results` con filtro `IN` y ordenación por columnas de una lista blanca, con `json_extract` para las métricas.
- **Tests**: nuevos tests de API para el filtro múltiple, la ordenación y los valores no válidos. Los tests existentes deben seguir pasando sin cambios.
- **Sin cambios** en el análisis, la CLI, los reportes CSV/JSON ni la imagen Docker (salvo reconstruirla).
- **Documentación**: la tabla de endpoints del README y las notas de frontend de `CLAUDE.md`.
