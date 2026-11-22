# Spec Delta

## MODIFIED Requirements

### Requirement: Consulta de resultados
La API SHALL devolver los resultados de un trabajo, completado o en curso, paginados y filtrables por una o varias clasificaciones y por formato. SHALL admitir ordenación en el servidor por gravedad, nombre, formato, bitrate, frecuencia de corte o presencia espectral, ascendente o descendente, con los valores ausentes al final. Sin parámetro de orden se mantiene el orden de llegada.

#### Scenario: Filtro por clasificación
- **WHEN** un cliente pide los resultados del trabajo filtrando por `fake`
- **THEN** solo recibe los resultados con esa clasificación

#### Scenario: Filtro por varias clasificaciones
- **WHEN** un cliente pide los resultados filtrando por `fake` y `suspicious` a la vez
- **THEN** recibe los resultados de ambas clasificaciones, y el total coincide con la suma de sus recuentos

#### Scenario: Orden por gravedad
- **WHEN** un cliente pide los resultados ordenados por gravedad
- **THEN** recibe primero los `fake`, después `suspicious`, `error` y `legitimate`, y dentro de cada grupo por nombre de archivo

#### Scenario: Orden que cruza páginas
- **WHEN** un cliente pide la segunda página ordenando por frecuencia de corte ascendente
- **THEN** todos sus valores son mayores o iguales que los de la primera página, y los resultados sin frecuencia de corte aparecen al final

#### Scenario: Compatibilidad con clientes existentes
- **WHEN** un cliente pide los resultados sin parámetros de orden ni filtros nuevos
- **THEN** recibe la misma respuesta que antes de este cambio, en orden de llegada

#### Scenario: Parámetro de orden no válido
- **WHEN** un cliente pide ordenar por un campo no admitido o por una clasificación inexistente
- **THEN** recibe un error 422 con un mensaje que indica los valores admitidos
