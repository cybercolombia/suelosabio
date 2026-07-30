# Auditoria municipal de precipitacion 2024-2025

**Fecha:** 29 de julio de 2026
**Producto:** `precipitacion_municipio_dia_2024_2025_v1`
**Contrato:** `precipitacion_municipio_dia_v1`
**Commit ejecutor:** `e76b1f6d00f94a998325e66499e75ddea3b488f0`
**Estado:** integridad aprobada; cobertura cientifica en revision

## Alcance

La corrida agrega precipitacion diaria por estacion a municipio para Boyaca y
Cundinamarca entre el 1 de enero de 2024 y el 31 de diciembre de 2025. Usa 116
estaciones canonicas de geografia v3, excluye nueve estaciones en revision y
una estacion de Bogota, y no imputa valores.

## Controles aprobados

| Control | Resultado |
|---|---:|
| Particiones departamento-ano-mes | 48 |
| Filas municipio-dia | 174.709 |
| Municipios objetivo | 239 |
| Fechas por municipio | 731 |
| Duplicados `codigo_municipio + fecha` | 0 |
| Estados validos con valor nulo | 0 |
| Estados no validos con valor principal | 0 |
| Duracion de la corrida | 51,64 s |

La salida coincide con el calendario completo de 239 municipios por 731 dias.
El manifiesto termino `COMPLETA`.

## Cobertura espacial

| Indicador | Resultado |
|---|---:|
| Municipios con al menos una estacion canonica utilizable | 84 (35,15 %) |
| Municipios sin estacion canonica utilizable | 155 (64,85 %) |
| Estaciones canonicas | 116 |
| Municipios con 1 estacion | 62 |
| Municipios con 2 estaciones | 17 |
| Municipios con 3 estaciones | 4 |
| Municipios con 8 estaciones | 1 |

Los 155 municipios no deben describirse como municipios donde nunca existio
una estacion IDEAM. No tienen una estacion del dataset de precipitacion que,
para 2024-2025, haya superado simultaneamente disponibilidad, calidad y
asignacion geografica canonica.

## Cobertura temporal y calidad

| Estado municipio-dia | Filas |
|---|---:|
| `SIN_ESTACIONES_CANONICAS` | 113.305 |
| `SIN_ESTACIONES_ESPERADAS_EN_FECHA` | 23.753 |
| `VALIDO_UNA_ESTACION` | 20.760 |
| `SIN_DATOS_ACEPTADOS` | 11.703 |
| `VALIDO_MULTIESTACION` | 5.096 |
| `COBERTURA_INSUFICIENTE` | 92 |

En los 84 municipios con red, hubo 37.651 municipio-dias con al menos una
estacion esperada y 25.856 dias validos: 68,67 % de cobertura agregada. La
mediana municipal de cobertura frente a dias esperados fue 75,46 %, pero la
variacion es amplia. Quetame, por ejemplo, tiene una estacion canonica y cero
dias aceptados en la ventana; tener una estacion no equivale a tener una serie
util.

## Decision

La construccion del artefacto queda aprobada: llaves, calendario, estados y
semantica de `NaN` son consistentes. El producto aun no habilita por si solo el
paso 08.

Antes de crear indicadores por periodo se debe:

- definir una cobertura temporal minima defendible;
- revisar los 92 municipio-dias con cobertura inferior a 50 %;
- evaluar dispersion e IQR en los 5.096 dias multiestacion;
- comparar media y mediana para medir sensibilidad;
- cruzar la cobertura con los municipios y cultivos finalmente presentes en
  EVA;
- mantener sin imputar los municipios o periodos sin evidencia suficiente.
