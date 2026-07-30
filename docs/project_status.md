# Estado vigente del proyecto RAIZ

**Actualizado:** 30 de julio de 2026
**Estado:** vigente
**Propósito:** fuente de verdad para alcance, datos disponibles y prioridades

Este documento debe leerse antes de planes anteriores, conversaciones o
recomendaciones preparadas para fechas límite ya vencidas.

## Objetivo vigente

RAIZ pronostica el rendimiento municipal de papa para los semestres A y B de
2026. El alcance de SCRUM-17 usa los diez municipios con mayor área sembrada
2024–2025 en Boyacá y los diez de Cundinamarca. El modelo se selecciona por
error absoluto medio en una validación temporal retrospectiva y se documenta en
[`../notebooks/CropForecasting/RESULTS.md`](../notebooks/CropForecasting/RESULTS.md).
SCRUM-18 consolida el ciclo técnico y la presentación en
[`data_pipeline/README.md`](data_pipeline/README.md) y
[`presentation/RESULTADOS_PROCESO_DATOS_2026.md`](presentation/RESULTADOS_PROCESO_DATOS_2026.md).

## Alcance confirmado

| Dimensión | Decisión vigente |
|---|---|
| Departamentos | Boyacá y Cundinamarca |
| Cultivo de pronóstico | Papa |
| Horizonte | 2026A y 2026B |
| Período climático predictivo | NASA POWER 2019–2026-07-30 |
| Período climático IDEAM curado | 2024–2025 |
| Fuente agrícola principal | EVA UPRA 2019–2025 |
| Unidad | Municipio + año + semestre + cultivo |
| Variable objetivo | Rendimiento en toneladas por hectárea |
| Modelo final v1 | Persistencia por municipio-semestre (`rendimiento_lag_1`) |
| Principio de datos | Crudos inmutables y productos derivados versionados |

Antioquia no forma parte del alcance. Sus resultados anteriores son pruebas
históricas de descarga y rendimiento de la interfaz de programación de
aplicaciones (API).

## Decisiones pendientes

- Validar el pronóstico 2026 cuando UPRA publique la variable objetivo observada.
- Decidir si una versión futura incorpora maíz u otros cultivos.
- Reentrenar cuando EVA 2026 esté disponible y recalibrar los intervalos.
- Resolver en paralelo las nueve estaciones geográficas no canónicas; no
  ingresan al agregado municipal mientras sigan pendientes.
- Revisar el desempeño más débil detectado en Cundinamarca-B.

## Datos climáticos disponibles

| Variable | Conjunto de datos | Alcance verificado | Estado |
|---|---|---|---|
| Precipitación | `s54a-sgyg` | 48 particiones 2024–2025 | 01–07 ejecutado; revisión científica municipal pendiente |
| Temperatura ambiente | `sbwg-7ju4` | 48 particiones 2024–2025 | Municipio-día completo |
| Temperatura mínima | `afdg-3zpb` | 48 particiones 2024–2025 | Municipio-día completo |
| Temperatura máxima | `ccvq-rp9s` | 48 particiones 2024–2025 | Municipio-día completo |
| Velocidad del viento | `sgfv-3yp8` | 48 particiones 2024–2025 | Municipio-día completo |
| Presión atmosférica | `62tk-nxj5` | 48 particiones 2024–2025 | Municipio-día completo |
| Humedad | `uext-mhny` | Crudo y auditoría parcial | Bloqueada antes de 03 |

La serie IDEAM conserva la brecha común del 5 al 25 de febrero de 2025 y los
municipios sin estación como ausencia. Para el pronóstico, NASA POWER aporta una
malla diaria completa 2019–2026; es una fuente distinta.

## Otros dominios del repositorio

| Dominio | Evidencia actual | Estado vigente |
|---|---|---|
| Agricultura | EVA UPRA 2019–2025 descargada, agregada y auditada para papa | Integrada en `notebooks/CropForecasting/` |
| Geografía | Catálogos IDEAM, DIVIPOLA y 239 polígonos municipales validados | V3 verificada: 116 canónicas, 9 revisiones y 1 exclusión |
| Suelos | `SoilData.ipynb` y cobertura 2020–2024 reportada | Exploratorio; no integrado al alcance analítico actual |
| Meteorología heredada | `MeteoData.ipynb` | Exploratorio; el pipeline activo está en `ClimatePipeline/` |

La presencia de un notebook no demuestra que su salida esté vigente, curada o
lista para integración. Estos archivos se revisarán antes de reutilizarlos.

## Estado del flujo climático

| Paso | Producto | Estado actual |
|---|---|---|
| 01 Descarga | `clima_crudo` | 48 particiones verificadas para seis variables; humedad parcial |
| 02 Auditoría cruda | Evidencia para reglas por variable | Ejecutada para seis variables; humedad incompleta |
| 03 Diario por sensor | `clima_diario_sensor` | Completo 2024–2025 para seis variables |
| 04 Auditoría diaria | `auditorias_clima_diario` | Completa para seis variables |
| 05 Consolidación | `clima_diario_curado` | Completa por estación-día para seis variables |
| 06 Geografía | `geografia_curada` | Canónica por variable; precipitación v3 conserva 9 revisiones y 1 exclusión |
| 07 Municipio diario | `clima_municipal` | Completo para seis variables; precipitación auditada con revisión pendiente |
| 08 Indicadores por período | `indicadores_climaticos` | Implementado para NASA POWER dentro de CropForecasting |
| 09 EVA | Agricultura curada y municipal | Auditorías y agregados ejecutados; 13.692 targets, 9.377 comparaciones y geografía completa; revisión taxonómica pendiente |
| Conjunto maestro y modelo | Tabla analítica y artefactos | Completo v1: 2.366 filas, 20 municipios objetivo y 40 pronósticos 2026 |

## Regla para nuevas variables

El notebook 02 diagnostica la variable cruda y produce evidencia. No define ni
aplica reglas automáticamente. A partir de esa evidencia se crea y prueba un
contrato propio para la variable antes de habilitarla en 03, 04 y 05.

La infraestructura de rutas, particiones, manifiestos y escritura segura puede
reutilizarse. Las reglas semánticas no: precipitación se acumula, mientras que
temperatura, humedad, presión y viento necesitan sus propias agregaciones,
umbrales y criterios de calidad.

## Prioridades actuales

1. Revisar la documentación y presentación consolidada de SCRUM-18.
2. Validar el resultado de Cundinamarca-B y la incertidumbre empírica.
3. Repetir el pronóstico cuando NASA POWER publique más días de 2026-B.
4. Validar contra EVA 2026 cuando UPRA publique las cifras oficiales.
5. Mantener en paralelo las auditorías IDEAM y las revisiones espaciales.

El orden completo y sus compuertas se mantienen en
[`project_roadmap.md`](project_roadmap.md). Las rutas y dependencias entre
productos se mantienen en [`data_artifacts.md`](data_artifacts.md). El avance
paso a paso de cada variable se actualiza en
[`climate_pipeline_status/README.md`](climate_pipeline_status/README.md).

## Alcances anteriores

Las expresiones `una variable`, `dos días restantes`, `entrega del martes` y
`papa + precipitación` pertenecen a planes de contingencia anteriores. Sirven
como contexto, pero no son decisiones vigentes salvo que se ratifiquen aquí.
