# Auditoria historica de precipitacion: Boyaca, 2021 y 2023

## Alcance

Las dos corridas usaron auditoria muestral, sin conteo completo de estaciones.
El inventario de archivos y filas es exacto por metadatos Parquet; duplicados,
valores, cadencias, estaciones y geografia corresponden a una muestra
estratificada de 48.000 filas por ano.

| Metrica | 2021 | 2023 |
|---|---:|---:|
| Archivos Parquet | 1.826 | 1.185 |
| Filas exactas | 1.819.899 | 1.178.461 |
| Tamano | 20,28 MB | 12,90 MB |
| Particiones mensuales | 12 | 12 |
| Archivos muestreados | 48 | 48 |
| Filas muestreadas | 48.000 | 48.000 |

No hubo partes faltantes ni errores de lectura. Las fechas internas de las 96.000
filas muestreadas coinciden con el ano y mes de sus carpetas.

## Esquema y unidad

Las 13 columnas esperadas aparecen en todos los archivos. En ambos anos se
repiten las dos variantes ya conocidas de `valorobservado`:

| Ano | Archivos `double` | Archivos `int64` |
|---:|---:|---:|
| 2021 | 1.817 | 9 |
| 2023 | 1.159 | 26 |

La unidad unica observada fue `mm`. No hubo nulos ni conversiones fallidas en
las muestras. `valorobservado` puede homologarse a decimal durante la lectura.

## Valores y duplicados

| Metrica muestral | 2021 | 2023 |
|---|---:|---:|
| Minimo | 0 mm | 0 mm |
| Mediana | 0 mm | 0 mm |
| Media | 0,02131 mm | 0,02176 mm |
| Percentil 99 | 0,4 mm | 0,5 mm |
| Maximo | 22,8 mm | 16,3 mm |
| Filas duplicadas exactas | 0 | 0 |
| Claves repetidas | 0 | 0 |
| Conflictos | 0 | 0 |

La ausencia de duplicados en estas muestras no demuestra que los anos completos
esten libres de ellos. En la muestra 2025 aparecieron 8.000 filas duplicadas, lo
que confirma que la duplicacion es intermitente y debe medirse por particion
durante el procesamiento diario.

## Cadencias y sensores

### 2021

| Sensor | Cadencia modal | Pares observados |
|---|---:|---:|
| `0240` | 5 minutos | 2 |
| `0240` | 10 minutos | 50 |
| `0240` | 60 minutos | 5 |

### 2023

| Sensor | Cadencia modal | Pares observados |
|---|---:|---:|
| `0257` | 2 minutos | 2 |
| `0240` | 5 minutos | 2 |
| `0240` | 10 minutos | 47 |

La cadencia de cinco minutos no habia aparecido en las auditorias de 2025. Se
observa en los mismos dos pares `0240` durante 2021 y 2023:

- Estacion `0023125501`, Pauna.
- Estacion `0024015501`, Bertha.

La repeticion en dos anos hace razonable tratar los 300 segundos como una
cadencia historica valida, no como un error automatico. Todavia debe conservarse
como diagnostico al procesar cada particion.

Los conteos de 57 estaciones en 2021 y 49 en 2023 son muestrales. No deben
interpretarse como inventarios anuales completos ni usarse para calcular
cobertura.

## Geografia

No se detectaron cambios de municipio ni desplazamientos superiores al umbral de
100 metros.

- En 2021 las 57 estaciones observadas conservaron nombre y coordenadas.
- En 2023 nueve de 49 estaciones presentaron variantes de nombre.
- El mayor desplazamiento de coordenadas en 2023 fue 63,31 metros.

Las variantes de nombre no cambian por si solas la asignacion municipal. Debe
usarse `codigoestacion` como identificador y conservar los nombres como atributos
observados.

## Volumen crudo no es lluvia

Boyaca contiene 1,82 millones de filas en 2021, 1,18 millones en 2023 y 2,31
millones en 2025. Los perfiles mensuales de filas no se correlacionan entre los
tres anos.

Este volumen depende de estaciones activas, cadencias, huecos y duplicados. No
puede usarse como indicador de cantidad de lluvia ni como evidencia de
estacionalidad.

## Consecuencias para el procesamiento diario

1. Aceptar inicialmente cadencias observadas de 120, 300, 600 y 3.600 segundos.
2. Deduplicar cada particion completa aunque una muestra historica no encuentre
   duplicados.
3. Agregar primero por estacion, sensor y dia.
4. No sumar sensores paralelos dentro de una estacion.
5. Calcular cobertura con la cadencia efectiva de cada par y periodo.
6. Conservar nombres y coordenadas observados para construir despues una tabla
   canonica de estaciones.
7. No comparar conteos crudos entre anos como si fueran precipitacion.

## Fuente

- [Precipitacion - Datos Abiertos Colombia](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg)
