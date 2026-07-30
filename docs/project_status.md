# Estado vigente del proyecto RAIZ

**Actualizado:** 30 de julio de 2026
**Estado:** vigente
**Proposito:** fuente de verdad para alcance, datos disponibles y prioridades

Este documento debe leerse antes de planes anteriores, conversaciones o
recomendaciones preparadas para fechas limite ya vencidas.

## Objetivo vigente

RAIZ pronostica el rendimiento municipal de papa para los semestres A y B de
2026. El alcance de SCRUM-17 usa los diez municipios con mayor area sembrada
2024-2025 en Boyaca y los diez de Cundinamarca. El modelo se selecciona por MAE
en backtesting temporal y se documenta en
[`../notebooks/CropForecasting/RESULTS.md`](../notebooks/CropForecasting/RESULTS.md).
SCRUM-18 consolida el ciclo técnico y la presentación en
[`data_pipeline/README.md`](data_pipeline/README.md) y
[`presentation/RESULTADOS_PROCESO_DATOS_2026.md`](presentation/RESULTADOS_PROCESO_DATOS_2026.md).

## Alcance confirmado

| Dimension | Decision vigente |
|---|---|
| Departamentos | Boyaca y Cundinamarca |
| Cultivo de pronostico | Papa |
| Horizonte | 2026A y 2026B |
| Periodo climatico predictivo | NASA POWER 2019-2026-07-30 |
| Periodo climatico IDEAM curado | 2024-2025 |
| Fuente agricola principal | EVA UPRA 2019-2025 |
| Unidad | Municipio + ano + semestre + cultivo |
| Target | Rendimiento en toneladas por hectarea |
| Modelo final v1 | Persistencia por municipio-semestre (`rendimiento_lag_1`) |
| Principio de datos | Crudos inmutables y productos derivados versionados |

Antioquia no forma parte del alcance. Sus resultados anteriores son pruebas
historicas de descarga y rendimiento de la API.

## Decisiones pendientes

- Validar el pronostico 2026 cuando UPRA publique el target observado.
- Decidir si una version futura incorpora maiz u otros cultivos.
- Reentrenar cuando EVA 2026 este disponible y recalibrar los intervalos.
- Resolver en paralelo las nueve estaciones geograficas no canonicas; no
  ingresan al agregado municipal mientras sigan pendientes.
- Revisar el desempeno mas debil detectado en Cundinamarca-B.

## Datos climaticos disponibles

| Variable | Dataset | Alcance verificado | Estado |
|---|---|---|---|
| Precipitacion | `s54a-sgyg` | 48 particiones 2024–2025 | 01–07 ejecutado; revisión científica municipal pendiente |
| Temperatura ambiente | `sbwg-7ju4` | 48 particiones 2024–2025 | Municipio-día completo |
| Temperatura minima | `afdg-3zpb` | 48 particiones 2024–2025 | Municipio-día completo |
| Temperatura maxima | `ccvq-rp9s` | 48 particiones 2024–2025 | Municipio-día completo |
| Velocidad del viento | `sgfv-3yp8` | 48 particiones 2024–2025 | Municipio-día completo |
| Presion atmosferica | `62tk-nxj5` | 48 particiones 2024–2025 | Municipio-día completo |
| Humedad | `uext-mhny` | Crudo y auditoría parcial | Bloqueada antes de 03 |

La serie IDEAM conserva la brecha común del 5 al 25 de febrero de 2025 y los
municipios sin estación como ausencia. Para el pronóstico, NASA POWER aporta una
malla diaria completa 2019–2026; es una fuente distinta.

## Otros dominios del repositorio

| Dominio | Evidencia actual | Estado vigente |
|---|---|---|
| Agricultura | EVA UPRA 2019-2025 descargada, agregada y auditada para papa | Integrada en `notebooks/CropForecasting/` |
| Geografia | Catalogos IDEAM, DIVIPOLA y 239 poligonos municipales validados | V3 verificada: 116 canonicas, 9 revisiones y 1 exclusion |
| Suelos | `SoilData.ipynb` y cobertura 2020-2024 reportada | Exploratorio; no integrado al alcance analitico actual |
| Meteorologia heredada | `MeteoData.ipynb` | Exploratorio; el pipeline activo esta en `ClimatePipeline/` |

La presencia de un notebook no demuestra que su salida este vigente, curada o
lista para integracion. Estos archivos se revisaran antes de reutilizarlos.

## Estado del pipeline climatico

| Paso | Producto | Estado actual |
|---|---|---|
| 01 Descarga | `clima_crudo` | 48 particiones verificadas para seis variables; humedad parcial |
| 02 Auditoria cruda | Evidencia para reglas por variable | Ejecutada para seis variables; humedad incompleta |
| 03 Diario por sensor | `clima_diario_sensor` | Completo 2024–2025 para seis variables |
| 04 Auditoria diaria | `auditorias_clima_diario` | Completa para seis variables |
| 05 Consolidacion | `clima_diario_curado` | Completa por estación-día para seis variables |
| 06 Geografia | `geografia_curada` | Canónica por variable; precipitación v3 conserva 9 revisiones y 1 exclusión |
| 07 Municipio diario | `clima_municipal` | Completo para seis variables; precipitación auditada con revisión pendiente |
| 08 Indicadores por periodo | `indicadores_climaticos` | Implementado para NASA POWER dentro de CropForecasting |
| 09 EVA | Agricultura curada y municipal | Auditorías y agregados ejecutados; 13.692 targets, 9.377 comparaciones y geografía completa; revisión taxonómica pendiente |
| Dataset maestro y modelo | Tabla analitica y artefactos | Completo v1: 2.366 filas, 20 municipios objetivo y 40 pronósticos 2026 |

## Regla para nuevas variables

El notebook 02 diagnostica la variable cruda y produce evidencia. No define ni
aplica reglas automaticamente. A partir de esa evidencia se crea y prueba un
contrato propio para la variable antes de habilitarla en 03, 04 y 05.

La infraestructura de rutas, particiones, manifiestos y escritura segura puede
reutilizarse. Las reglas semanticas no: precipitacion se acumula, mientras que
temperatura, humedad, presion y viento necesitan sus propias agregaciones,
umbrales y criterios de calidad.

## Prioridades actuales

1. Revisar la documentación y presentación consolidada de SCRUM-18.
2. Validar el resultado de Cundinamarca-B y la incertidumbre empirica.
3. Repetir el pronostico cuando NASA POWER publique mas dias de 2026-B.
4. Validar contra EVA 2026 cuando UPRA publique las cifras oficiales.
5. Mantener en paralelo las auditorias IDEAM y las revisiones espaciales.

El orden completo y sus compuertas se mantienen en
[`project_roadmap.md`](project_roadmap.md). Las rutas y dependencias entre
productos se mantienen en [`data_artifacts.md`](data_artifacts.md). El avance
paso a paso de cada variable se actualiza en
[`climate_pipeline_status/README.md`](climate_pipeline_status/README.md).

## Alcances anteriores

Las expresiones `una variable`, `dos dias restantes`, `entrega del martes` y
`papa + precipitacion` pertenecen a planes de contingencia anteriores. Sirven
como contexto, pero no son decisiones vigentes salvo que se ratifiquen aqui.
