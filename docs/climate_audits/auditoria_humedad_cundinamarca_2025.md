# Auditoria climatica: humedad, Cundinamarca, 2025

## Identificacion

| Campo | Valor |
|---|---|
| Variable | Humedad relativa |
| Fuente Socrata | `uext-mhny` |
| Departamento | Cundinamarca |
| Periodo | 2025, meses 1 a 12 |
| Commit con resultados | `3efb262` |
| Modo | Muestra estratificada y conteo completo por estacion/sensor |

Aunque el mensaje del commit menciona 2023, la configuracion guardada y las
particiones auditadas corresponden a 2025.

## Alcance exacto

- 633 archivos Parquet.
- 627.529 filas segun metadatos Parquet.
- 10,24 MB.
- 12 particiones mensuales.
- Sin partes faltantes ni archivos ilegibles.
- Las 13 columnas esperadas aparecen en todos los archivos.

| Mes | Archivos | Filas |
|---:|---:|---:|
| 1 | 80 | 79.454 |
| 2 | 12 | 11.524 |
| 3 | 37 | 36.815 |
| 4 | 37 | 36.672 |
| 5 | 37 | 36.006 |
| 6 | 48 | 47.454 |
| 7 | 63 | 62.359 |
| 8 | 48 | 47.646 |
| 9 | 51 | 50.681 |
| 10 | 64 | 63.469 |
| 11 | 75 | 74.837 |
| 12 | 81 | 80.612 |

La densidad mensual maxima es aproximadamente siete veces la minima. Esto no se
debe interpretar como un ciclo climatico sin revisar primero estaciones activas,
frecuencias y cobertura.

## Esquema y tipos

Se encontraron dos firmas de esquema. La unica diferencia observada es
`valorobservado`:

- `double` en 621 archivos.
- `int64` en 12 archivos.

Ambos tipos son numericos y pueden homologarse sin perdida aparente a un tipo
decimal durante la lectura.

## Muestra de calidad

La muestra estratificada incluyo 48 archivos y 48.000 filas, equivalentes al
7,65 % de las filas del periodo.

- Sin nulos en las 13 columnas.
- Sin conversiones fallidas de fecha, valor, latitud o longitud.
- Sin coordenadas fuera de rango.
- Sin diferencias entre el departamento del dato y la particion.
- Unidad unica: `%`.
- Valor minimo: 0.
- Mediana: 95.
- Media: 88,79.
- Percentiles p95 y p99: 100.
- Valor maximo: 100.

La concentracion en 100 puede representar saturacion real, redondeo o tope del
sensor. Debe cuantificarse antes de definir reglas de valores atipicos.

## Duplicados

- 6.000 filas pertenecen a duplicados exactos, el 12,5 % de la muestra.
- Se encontraron 3.000 claves repetidas.
- No se encontraron claves repetidas con valores observados distintos.

El patron observado corresponde a pares identicos. Es razonable proponer una
deduplicacion exacta antes del agregado diario, pero la prevalencia debe medirse
por particion durante el procesamiento completo.

## Estaciones y frecuencia

El conteo completo recorrio los 633 archivos leyendo estacion, sensor y fecha.
La combinacion con mayor volumen fue:

| Estacion | Sensor | Registros | Fecha minima | Fecha maxima |
|---|---|---:|---|---|
| `3502500135` | `0028` | 263.772 | 2025-01-01 00:00 | 2025-12-31 23:58 |

La muestra presento tres cadencias modales. En los resultados visibles aparecen
10 minutos y 1 hora. Una tercera cadencia probablemente corresponde a 2 minutos,
inferencia consistente con el volumen del sensor `0028`; debe confirmarse de
forma explicita antes de usarla como regla.

La frecuencia distinta entre sensores confirma que el numero bruto de filas no
puede usarse como peso durante una agregacion diaria.

## Geografia

El auditor marco 13 estaciones con geografia variable. Esta alerta es sensible a
cualquier diferencia en coordenadas redondeadas al quinto decimal, incluso si es
muy pequena. No se debe interpretar todavia como traslado de estaciones.

La regla debe mejorarse para medir distancia y separar variaciones de precision
de cambios geograficos relevantes.

## Decisiones preliminares

1. Conservar los Parquet crudos sin cambios.
2. Homologar `valorobservado` como numerico durante el procesamiento.
3. Deduplicar filas exactas antes de calcular estadisticas diarias.
4. No promediar sensores entre si antes de calcular cobertura individual.
5. Definir cobertura diaria segun la cadencia observada de cada sensor.
6. Conservar conteos de observaciones y banderas de calidad por dia.
7. Refinar el control geografico usando una distancia minima significativa.
8. No imputar observaciones subdiarias en esta etapa.

