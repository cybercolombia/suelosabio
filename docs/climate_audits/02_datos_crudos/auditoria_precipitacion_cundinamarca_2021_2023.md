# Auditoria historica de precipitacion: Cundinamarca, 2021 y 2023

## Alcance

Las dos corridas usaron auditoria muestral, sin conteo completo de estaciones.
El inventario de archivos y filas es exacto por metadatos Parquet; duplicados,
valores, cadencias, estaciones y geografia corresponden a una muestra
estratificada de 48.000 filas por ano.

| Metrica | 2021 | 2023 |
|---|---:|---:|
| Archivos Parquet | 1.603 | 1.294 |
| Filas exactas | 1.595.902 | 1.287.261 |
| Tamano | 17,82 MB | 16,68 MB |
| Particiones mensuales | 12 | 12 |
| Archivos muestreados | 48 | 48 |
| Filas muestreadas | 48.000 | 48.000 |

No hubo partes faltantes ni errores de lectura. Las fechas internas de las 96.000
filas muestreadas coinciden con el ano y mes de sus carpetas.

## Esquema, unidad y valores

Las 13 columnas esperadas aparecen en todos los archivos. La unica variante de
tipo corresponde a `valorobservado`:

| Ano | Archivos `double` | Archivos `int64` |
|---:|---:|---:|
| 2021 | 1.593 | 10 |
| 2023 | 1.129 | 165 |

La unidad unica fue `mm`. No hubo nulos ni conversiones fallidas.

| Metrica muestral | 2021 | 2023 |
|---|---:|---:|
| Minimo | 0 mm | 0 mm |
| Mediana | 0 mm | 0 mm |
| Media | 0,07892 mm | 0,01684 mm |
| Percentil 99 | 0,8 mm | 0,3 mm |
| Maximo | 28,5 mm | 28,4 mm |
| Filas duplicadas exactas | 0 | 0 |
| Claves repetidas | 0 | 0 |
| Conflictos | 0 | 0 |

Las medias no representan lluvia departamental porque cada muestra contiene
fragmentos de estaciones, dias y cadencias diferentes. La ausencia de duplicados
no se extrapola al ano completo: la muestra de 2025 demostro duplicacion
intermitente.

## Cadencias y sensores

### 2021

| Sensor | Cadencia modal | Pares observados |
|---|---:|---:|
| `0240` | 5 minutos | 3 |
| `0240` | 10 minutos | 44 |
| `0240` | 60 minutos | 16 |

### 2023

| Sensor | Cadencia modal | Pares observados |
|---|---:|---:|
| `0240` | 1 minuto | 1 |
| `0257` | 1 minuto | 1 |
| `0240` | 5 minutos | 1 |
| `0240` | 10 minutos | 45 |

La cadencia de cinco minutos confirma el hallazgo historico de Boyaca. La
cadencia de un minuto se concentra en la estacion `3502500135`, Guayabetal Pollo
Olimpico, donde coexisten `0240` y `0257`.

Una consulta directa al API oficial entre las 10:00 y 10:20 del 24 de septiembre
de 2023 devolvio ambos sensores en cada minuto, cada uno con un identificador
Socrata distinto. La frecuencia no es un artefacto del muestreo ni de los
Parquet.

Por tanto, la cadencia no debe fijarse globalmente por codigo de sensor. Debe
inferirse y registrarse por estacion, sensor y periodo. Las frecuencias
observadas en el proyecto son 60, 120, 300, 600 y 3.600 segundos.

## Geografia

La muestra 2021 no presento variacion geografica. En 2023 aparecieron dos
estaciones por encima del umbral de 100 metros:

| Estacion | Municipio observado | Variacion aproximada |
|---|---|---:|
| `0021209920` | Suesca | 10.010,55 m |
| `3502500135` | Guayabetal | 520,75 m |

Ambas conservaron municipio, pero el desplazamiento impide escoger una
coordenada canonica de forma automatica. La estacion de Suesca requiere revision
prioritaria antes de cualquier asignacion espacial fina.

Tambien se observaron cinco estaciones con variantes de nombre en 2023. El
procesamiento diario debe conservar `codigoestacion` como clave y no depender del
nombre o de una coordenada unica.

## Comparacion temporal y territorial

Los conteos mensuales entre Boyaca y Cundinamarca presentan correlacion de 0,687
en 2021, 0,969 en 2023 y 0,988 en 2025. Esto sugiere cambios sistemicos de
cobertura o publicacion dentro de cada ano.

En cambio, los perfiles mensuales de un mismo departamento no se correlacionan
entre anos. El numero de filas crudas no mide precipitacion ni estacionalidad.

## Contrato preliminar para el procesamiento diario

1. Interpretar `valorobservado` como incremento de precipitacion del intervalo,
   con unidad `mm`, bajo una regla preliminar versionada.
2. Convertir `valorobservado` a decimal y conservar valores no negativos.
3. Deduplicar filas exactas dentro de cada particion completa.
4. No promediar claves repetidas con valores conflictivos; reportarlas.
5. Agregar por estacion, sensor y dia mediante suma.
6. Mantener sensores paralelos separados y escoger uno en una etapa posterior.
7. Inferir la cadencia por estacion, sensor y periodo; no fijarla por codigo.
8. No imputar observaciones subdiarias ni eliminar extremos en esta capa.
9. Conservar fecha, nombre, municipio y coordenadas observadas para trazabilidad.
10. Usar el dia calendario publicado por la fuente sin conversion de zona horaria
    hasta disponer de metadatos temporales mas precisos.

Este contrato permite iniciar el piloto diario. La cobertura minima aceptable y
la seleccion del sensor canonico se definiran auditando esa nueva capa.

## Fuente

- [Precipitacion - Datos Abiertos Colombia](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg)
