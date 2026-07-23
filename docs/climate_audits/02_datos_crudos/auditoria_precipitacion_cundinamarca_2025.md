# Auditoria climatica: precipitacion, Cundinamarca, 2025

## Identificacion

| Campo | Valor |
|---|---|
| Variable | Precipitacion |
| Fuente Socrata | `s54a-sgyg` |
| Departamento | Cundinamarca |
| Periodo | 2025, meses 1 a 12 |
| Commit con resultados | `a9ba98b` |
| Modo | Muestra estratificada y conteo completo por estacion/sensor |

La auditoria se ejecuto con dos bloques aleatorios de dos archivos contiguos por
particion mensual. El conteo completo leyo estacion, sensor y fecha de todos los
archivos seleccionados.

## Alcance exacto

- 2.312 archivos Parquet.
- 2.304.482 filas segun metadatos Parquet.
- 27,13 MB.
- 12 particiones mensuales.
- Sin partes faltantes ni archivos ilegibles.
- Las 13 columnas esperadas aparecen en todos los archivos.

| Mes | Archivos | Filas | Tamano MB |
|---:|---:|---:|---:|
| 1 | 351 | 350.584 | 3,85 |
| 2 | 38 | 37.716 | 0,43 |
| 3 | 143 | 142.234 | 1,69 |
| 4 | 137 | 136.385 | 1,62 |
| 5 | 154 | 153.038 | 1,81 |
| 6 | 198 | 197.399 | 2,34 |
| 7 | 202 | 201.108 | 2,38 |
| 8 | 193 | 192.113 | 2,28 |
| 9 | 198 | 197.699 | 2,35 |
| 10 | 237 | 236.293 | 2,85 |
| 11 | 225 | 224.722 | 2,70 |
| 12 | 236 | 235.191 | 2,83 |

La diferencia entre enero y febrero es superior a nueve veces. Una consulta
directa posterior a Socrata confirmo que esta variacion no fue creada por las
particiones locales. Para la estacion `0021205670`, sensor `0240`, la fuente
devolvio 8.856 registros en enero, 1.556 en febrero y 4.384 en marzo de 2025.
La fuente contiene tanto duplicacion como huecos de cobertura variables por mes.

## Esquema y tipos

Se encontraron dos firmas de esquema. La unica diferencia es
`valorobservado`:

- `double` en 2.174 archivos.
- `int64` en 138 archivos.

Ambos tipos pueden homologarse a un tipo decimal durante la lectura. Las demas
columnas conservaron el mismo tipo en todos los archivos.

## Muestra de calidad

La muestra estratificada incluyo 48 archivos y 47.113 filas, equivalentes al
2,04 % del periodo inventariado.

- Sin nulos en las 13 columnas.
- Sin conversiones fallidas de fecha, valor, latitud o longitud.
- Sin coordenadas fuera de rango.
- Sin diferencias entre departamento del dato y particion.
- Unidad unica: `mm`.
- Valor minimo: 0 mm.
- Mediana: 0 mm.
- Media: 0,0222 mm.
- Percentil 95: 0 mm.
- Percentil 99: 0,4 mm.
- Maximo: 29 mm.

La gran proporcion de ceros es compatible con observaciones de precipitacion
subdiaria, pero la muestra no basta para definir rangos fisicos de exclusion.

## Duplicados

- 7.996 filas pertenecen a duplicados exactos.
- Representan el 16,97 % de la muestra.
- Forman 3.998 pares o grupos duplicados.
- Eliminar una copia por cada par retiraria 3.998 filas, el 8,49 % de la muestra.
- No se observaron claves repetidas con valores distintos.

El descargador ordena por fecha, estacion, sensor y el identificador interno
unico `:id`. Por tanto, el patron no parece provenir de limites inestables entre
lotes de 1.000 filas.

Una consulta oficial de una hora para la estacion `3502500135` mostro dos filas
identicas por timestamp para los sensores `0240` y `0257`. Otra ventana de abril
no presento esa duplicacion. La duplicacion es intermitente en la fuente y debe
medirse por particion, estacion y sensor antes de extrapolar el 16,97 % al total.

## Sensores y frecuencia

El conteo completo esta inflado por duplicados, pero permite observar rangos
temporales. La combinacion con mas filas fue:

| Estacion | Sensor | Registros crudos | Fecha minima | Fecha maxima |
|---|---|---:|---|---|
| `3502500135` | `0257` | 263.736 | 2025-01-01 00:00 | 2025-12-31 23:58 |

La muestra detecto tres cadencias modales. Los resultados visibles confirman:

- Sensor `0240`: descripcion `PRECIPITACION`, normalmente cada 10 minutos.
- Sensor `0257`: descripcion `GPRS - PRECIPITACION`, normalmente cada 2 minutos.

El sensor `0257` produjo aproximadamente 722,6 filas crudas por dia, cerca de
las 720 esperadas para una cadencia de dos minutos, pero la diferencia no puede
interpretarse como mayor cobertura antes de deduplicar.

La tabla de observaciones diarias calculada sobre la muestra no mide cobertura
diaria real. Los bloques de archivos contienen fragmentos de dias y estaciones;
por eso sus medianas, cercanas a 40 registros para sensores de 10 minutos, no
deben compararse directamente con las 144 observaciones teoricas de un dia.

## Sensores paralelos

La estacion `3502500135` contiene simultaneamente los sensores `0240` y `0257`.
En dos eventos consultados, ambos reportaron el mismo valor de 1,9 mm con pocos
minutos de diferencia. Esto sugiere canales paralelos o redundantes y demuestra
que no deben sumarse sensores de una misma estacion.

La equivalencia no es perfecta. En una ventana del 10 de abril, `0240` reporto
18,8 mm a las 03:21 mientras `0257` permanecio en cero. No se debe eliminar
globalmente uno de los codigos sin comparar cobertura y comportamiento por
periodo.

La secuencia correcta debe ser:

```text
deduplicar filas exactas
  -> calcular precipitacion diaria por estacion y sensor
  -> comparar sensores coexistentes dentro de la estacion
  -> escoger o consolidar con una regla de calidad
  -> combinar estaciones a nivel municipal
```

## Semantica de valor observado

La pagina oficial describe el dataset como cantidad de lluvia registrada cada
10 minutos. Los patrones observados, la unidad en milimetros y el regreso a cero
despues de valores positivos son compatibles con incrementos por intervalo, no
con un contador acumulado monotono.

Esta lectura es una inferencia respaldada por muestras, no una definicion tecnica
completa del instrumento. Antes de fijar la suma diaria se debe contrastar mas de
una estacion y buscar documentacion oficial del sensor o del proceso de
publicacion.

## Geografia

El auditor marco 19 estaciones con geografia variable. Varias diferencias son
pequenas, pero algunas coordenadas cambian varios cientos de metros y una
estacion de la muestra aparece asociada con dos municipios.

La regla actual cuenta cualquier coordenada distinta al quinto decimal. Debe
reemplazarse por distancia en metros y por una tabla canonica de estacion antes
de asignar definitivamente municipios.

## Evaluacion general

La fuente es util y procesable, pero no esta lista para una suma diaria ingenua.
Sus fortalezas son:

- Todas las particiones locales son legibles y no tienen huecos de archivos.
- El esquema es estable salvo por un tipo numerico compatible.
- No hay nulos ni fallos de conversion en la muestra.
- Las unidades son consistentes.
- La cobertura anual incluye numerosos sensores y estaciones.

Sus riesgos principales son:

- Duplicados exactos abundantes e intermitentes.
- Huecos mensuales de cobertura.
- Frecuencias distintas entre sensores.
- Sensores paralelos dentro de una estacion.
- Variacion geografica que requiere una regla espacial significativa.
- Semantica de la medicion aun no cerrada documentalmente.

## Decisiones para el siguiente paso

1. Conservar los Parquet crudos sin cambios.
2. Homologar `valorobservado` como decimal.
3. Deduplicar filas exactas antes de calcular conteos o lluvia.
4. Reportar duplicados por mes, estacion y sensor.
5. No sumar sensores dentro de una estacion.
6. Calcular cobertura diaria sobre particiones completas, no sobre la muestra.
7. Comparar sensores coexistentes y definir una preferencia trazable.
8. Verificar fecha minima y maxima reales dentro de cada carpeta mensual.
9. Medir estaciones activas por mes para explicar cambios de densidad.
10. Confirmar la semantica incremental en varias estaciones antes de sumar por
    dia.

## Fuente

- [Precipitacion - Datos Abiertos Colombia](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg)
