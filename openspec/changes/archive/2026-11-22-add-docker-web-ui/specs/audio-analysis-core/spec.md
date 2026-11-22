# Spec Delta

## Purpose

Analizar archivos de audio y clasificarlos como legítimos, fake, sospechosos o error mediante un servicio reutilizable que comparten la CLI y la interfaz web, con resultados estructurados y reportes exportables.

## ADDED Requirements

### Requirement: Resultado estructurado por archivo
El sistema SHALL producir, por cada archivo analizado, un resultado que incluya como mínimo: nombre y ruta del archivo, formato, clasificación (`legitimate`, `fake`, `suspicious` o `error`), razón legible en español, bitrate en bps, sample rate, frecuencia de corte, presencia espectral 18–22 kHz, energía en altas frecuencias, presencia de contenido >20 kHz, rango dinámico y tamaño del archivo.

#### Scenario: Archivo válido analizado
- **WHEN** se analiza un archivo FLAC, WAV o MP3 legible
- **THEN** el resultado contiene todos los campos indicados con la clasificación y la razón producidas por el algoritmo de detección vigente

#### Scenario: Métrica no calculable
- **WHEN** una métrica no se puede calcular para un archivo
- **THEN** el campo correspondiente tiene valor nulo en lugar de omitirse

### Requirement: Errores aislados por archivo
Un fallo al leer o analizar un archivo MUST quedar registrado como resultado con clasificación `error` y una razón descriptiva, sin detener el análisis del resto de archivos.

#### Scenario: Archivo corrupto dentro de un lote
- **WHEN** un lote contiene un archivo que no se puede decodificar
- **THEN** ese archivo obtiene clasificación `error` y el resto del lote se analiza con normalidad

### Requirement: Clasificación sin cambios respecto a la versión actual
Con las mismas entradas, el servicio SHALL producir la misma clasificación y la misma razón que el algoritmo híbrido v2.0 actual. Sus umbrales y su comportamiento no se modifican.

#### Scenario: Regresión del detector
- **WHEN** se evalúan los casos de prueba existentes del detector
- **THEN** todos producen la misma clasificación que antes del cambio

### Requirement: Informe de progreso
Al analizar un conjunto de archivos, el sistema SHALL informar del progreso después de cada archivo, indicando los archivos completados, el total y el resultado del último archivo.

#### Scenario: Progreso durante un lote
- **WHEN** se analiza un lote de N archivos
- **THEN** se emiten N notificaciones de progreso con el contador de completados aumentando de 1 en 1 hasta N

### Requirement: Exportación de reportes sin efectos secundarios
El sistema SHALL generar reportes CSV y JSON a partir de los mismos resultados, en cualquier orden, sin alterar los datos de origen. En el CSV el bitrate se muestra en kbps y en el JSON se conserva el valor numérico.

#### Scenario: CSV seguido de JSON
- **WHEN** se exporta primero a CSV y después a JSON el mismo conjunto de resultados
- **THEN** el JSON contiene `bitrate` como número en bps, idéntico al de los resultados originales

#### Scenario: Contenido del CSV
- **WHEN** se exporta a CSV
- **THEN** el archivo, codificado en UTF-8, incluye cabecera y una fila por resultado, con al menos nombre, ruta, clasificación, razón, formato, bitrate (kbps), sample rate, frecuencia de corte, presencia espectral, rango dinámico y tamaño

### Requirement: Compatibilidad de la CLI
La CLI SHALL conservar las opciones actuales (`--path`, `--recursive/--no-recursive`, `--formats`, `--output`, `--json`, `--verbose`), su salida en consola y sus marcadores ASCII (`[OK]`, `[X]`, `[!]`, `[ERR]`).

#### Scenario: Ejecución de la CLI tras el cambio
- **WHEN** se ejecuta `python -m src.main -p <dir> -o r.csv -j r.json`
- **THEN** se muestran los resultados y el resumen en consola como antes y se generan ambos reportes

### Requirement: Versión única de la aplicación
La aplicación SHALL exponer un único número de versión, el mismo en la cabecera de la CLI, en la API y en la interfaz web.

#### Scenario: Consulta de versión
- **WHEN** se comparan la versión mostrada por la CLI y la que devuelve la API
- **THEN** ambas coinciden
