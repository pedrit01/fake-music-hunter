# Tasks

Todo se ejecuta en Docker, con los comandos de `CLAUDE.md`:
- Tests: `docker run --rm -v "$PWD":/app fmh-dev pytest`.
- Build del frontend: `npm run build`, en `node:22-alpine` con el volumen `fmh-node-modules`.

## 1. API: filtro múltiple y ordenación en el servidor

- [x] 1.1 En `src/web/store.py`, ampliar `list_results`:
  - Aceptar una lista de clasificaciones (`IN`).
  - Aceptar una clave de orden y un sentido, traducidos con un diccionario fijo a expresiones SQL: `CASE` para gravedad y `json_extract` para las métricas.
  - Mantener los nulos al final y el desempate `file_name, idx`.
  - Sin clave de orden, mantener `ORDER BY idx`.

  Verificar con tests nuevos en `tests/web/test_settings_store_paths.py`: varias clasificaciones, orden por gravedad, orden por `cutoff_frequency` ascendente y descendente con nulos al final, y paginación sin filas repetidas.
- [x] 1.2 En `src/web/routes/jobs.py`, aceptar en `GET /api/jobs/{id}/results`:
  - `classification` como lista de valores válidos.
  - `sort` (lista blanca) y `order` (`asc`/`desc`).

  Verificar con tests nuevos en `tests/web/test_api.py`:
  - `classification=fake&classification=suspicious` devuelve la suma de ambos.
  - `sort=severity` devuelve primero los fakes.
  - Una clasificación inexistente o un `sort` no admitido devuelven 422.
  - Una petición sin parámetros nuevos responde igual que antes.

  Todos los tests existentes deben seguir pasando.
- [x] 1.3 Documentar los parámetros nuevos en la tabla de endpoints del README y en la sección `web/` de `CLAUDE.md`. Verificar con `curl` contra la API en Docker que los ejemplos del README funcionan tal cual.

## 2. Tabla de resultados: problemas primero

- [x] 2.1 En `frontend/src/api/types.ts` y `client.ts`:
  - `ResultFilters` pasa a usar `classification: Classification[]`, `sort` y `order`.
  - `withQuery` serializa los parámetros repetidos.

  Verificar con `npm run typecheck`.
- [x] 2.2 En `ResultsTable.tsx`:
  - Orden en el servidor, con valor inicial `severity` ascendente y el orden dentro de la `queryKey`.
  - Eliminar `sortRows`.
  - La cabecera "Clasificación" ordena por gravedad.
  - El `select` de clasificación gana la opción "Solo problemas".
  - Cambiar de orden vuelve a la primera página.

  Verificar contra la biblioteca de prueba en Docker:
  - Un trabajo de 82 archivos empieza por los 3 Fake y los 2 Sospechoso.
  - "Solo problemas" muestra 5 archivos.
  - Ordenar por "Corte" ascendente lleva los cortes más bajos a la primera página.
- [x] 2.3 Adaptar `JobPage.tsx` y `Summary.tsx` al filtro en forma de lista:
  - Pulsar una tarjeta selecciona solo esa clasificación y volver a pulsarla la quita.
  - Las tarjetas con 0 usan la clase `empty`.

  Verificar en el navegador que el recuento del filtro coincide con el de la tarjeta y que "Error 0" aparece atenuada en claro y en oscuro.

## 3. Título de la pestaña

- [ ] 3.1 Crear `hooks/useDocumentTitle.ts` y usarlo en `NewAnalysisPage`, `HistoryPage` y `JobPage`:
  - Formato `<página> · Fake Music Hunter`.
  - En un trabajo en curso, `NN % · Analizando…` con porcentaje entero.
  - Al terminar, el estado final.

  Verificar con Playwright que el título cambia durante un análisis real y muestra "Completado" al final.

## 4. Accesibilidad

- [ ] 4.1 En `ResultsTable.tsx`, convertir el nombre del archivo en un `<button>` con `aria-expanded` y `aria-controls` hacia la fila de detalle. La fila conserva el clic con el ratón, sin alternar el detalle dos veces. Verificar con Playwright que Tab y Enter abren el detalle y Enter lo cierra.
- [ ] 4.2 En `LibraryBrowser.tsx`, agrupar los formatos en `<fieldset>` con `<legend>Formatos</legend>`. Ajustar `styles.css` para que los controles pequeños tengan una zona de toque de al menos 24 × 24 px:
  - `label.check`
  - checkboxes de 18 px
  - `.link-button` (migas de pan y "Quitar" de la subida)

  Verificar con Playwright, midiendo con `getBoundingClientRect`, que esos controles miden al menos 24 px de alto a 360 px de ancho.
- [ ] 4.3 Añadir `aria-label` a las barras de progreso de `JobPage` y `UploadPanel`. Añadir `@media (prefers-reduced-motion: reduce)`, que anula transiciones y animaciones. Verificar con Playwright, emulando `reducedMotion: "reduce"`, que la barra no tiene `transition`.

## 5. Móvil y pulido visual

- [ ] 5.1 Por debajo de 640 px, la tabla de resultados oculta el motivo (`.result-reason`) y muestra la frecuencia de corte en la fila (`.mobile-only`). Verificar con una captura a 360 px:
  - Cada resultado ocupa una fila.
  - No hay scroll horizontal.
  - La página de 50 resultados es mucho más corta que los ~6.800 px actuales.
  - El detalle desplegable sigue mostrando el motivo.
- [ ] 5.2 Crear `components/Icon.tsx` con iconos SVG propios (`music`, `folder`, `arrow-up`, `x`), con `aria-hidden` y `currentColor`. Sustituir los emojis de `App.tsx`, `LibraryBrowser.tsx` y `UploadPanel.tsx`. Verificar que ya no quedan emojis en `frontend/src` con `grep -P "[\x{1F300}-\x{1FAFF}\x{2B06}]"` y que los iconos se ven en claro y en oscuro.
- [ ] 5.3 En las tablas de resultados e historial:
  - Alinear a la derecha las columnas numéricas y sus cabeceras, con `tabular-nums`.
  - En el navegador de carpetas, sustituir la lista vacía con borde por un texto discreto cuando no hay subcarpetas ni carpeta padre.

  Verificar con capturas de escritorio en claro y oscuro.

## 6. Verificación final

- [ ] 6.1 Ejecutar `pytest` completo y `npm run build` en Docker sin errores. Reconstruir la imagen con `docker build -t fake-music-hunter .` y repetir la prueba E2E de Playwright contra ella, actualizada a los nuevos comportamientos. Revisar las capturas de escritorio, oscuro y móvil.
- [ ] 6.2 Añadir la entrada correspondiente al `CHANGELOG.md` (mejoras de la interfaz y parámetros nuevos de la API). Verificar que `openspec validate improve-web-ui-ux --strict` pasa.

## Workflow follow-up

- Archivar la change con `/openspec-archive-change` tras revisar y hacer commit.
