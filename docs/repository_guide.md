# Guia del repositorio

**Actualizado:** 30 de julio de 2026
**Estado:** inventario vigente; revision de codigo pendiente

Esta guia orienta a personas y asistentes de IA. Clasifica los archivos por su
funcion actual, pero no garantiza que los notebooks heredados ejecuten de
principio a fin. La futura revision de scripts debe actualizar este documento.

## Pipeline climatico activo

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `ClimatePipeline/01_Climate_<Variable>_DataDownloader.ipynb` | Descargar Socrata por departamento, año y mes | Seis variables con 48 particiones 2024–2025 |
| `ClimatePipeline/02_Climate_<Variable>_DataAudit.ipynb` | Auditar crudos y generar evidencia | Ejecutado para seis variables |
| `ClimatePipeline/03_Climate_<Variable>_DailyProcessor.ipynb` | Producir estación-sensor-día | Ejecutado para seis variables |
| `ClimatePipeline/04_Climate_<Variable>_DailyAudit.ipynb` | Auditar la capa diaria preliminar | Ejecutado para seis variables |
| `ClimatePipeline/05_Climate_<Variable>_DailyConsolidator.ipynb` | Producir estación-día canónico | Ejecutado para seis variables |
| `ClimatePipeline/06_Climate_<Variable>_GeographyAudit.ipynb` | Validar estaciones contra DIVIPOLA y polígonos | Ejecutado para seis variables |
| `ClimatePipeline/07_Climate_<Variable>_MunicipalAggregator.ipynb` | Producir municipio-día con cobertura | Ejecutado para seis variables |
| `ClimatePipeline/07_2_Climate_Precipitation_MunicipalAudit.ipynb` | Auditar cobertura y sensibilidad de precipitación | Ejecutado; revisión científica pendiente |

`<Variable>` representa precipitación, temperatura ambiente, mínima, máxima,
velocidad del viento o presión atmosférica. Los notebooks quedan protegidos por
banderas `EJECUTAR_*` en `False` dentro de Git. Humedad no tiene notebooks 03–07
porque su contrato sigue bloqueado.

## Modulos y pruebas activos

| Archivo | Funcion |
|---|---|
| `ClimateProcessingUtils.py` | Rutas, particiones, Unicode, tiempos, manifiestos y escrituras seguras |
| `PrecipitationRules.py` | Contrato subdiario a estacion-sensor-dia de precipitacion |
| `PrecipitationDailyAudit.py` | Calendario y diagnostico diario de precipitacion |
| `PrecipitationDailyConsolidation.py` | Contrato estacion-dia de precipitacion |
| `ClimateGeography.py` | Cruce trazable de estaciones, catalogo IDEAM y DIVIPOLA |
| `PrecipitationMunicipalAggregation.py` | Contrato estacion-dia a municipio-dia de precipitacion |
| `PrecipitationMunicipalAudit.py` | Cobertura por periodo y sensibilidad media-mediana municipal |
| `TemperatureRules.py` | Contratos diarios de temperatura ambiente, minima y maxima |
| `TemperatureDailyAudit.py` | Calendario y diagnostico diario de temperatura |
| `HumidityRules.py` | Marcador bloqueante hasta definir reglas de humedad |
| `HumidityDailyAudit.py` | Marcador bloqueante hasta definir la auditoria diaria de humedad |
| `ScalarClimateRules.py` | Contrato compartido de presión y viento |
| `ScalarDailyAudit.py` | Auditoría diaria compartida de variables escalares |
| `ScalarDailyConsolidation.py` | Consolidación estación-día compartida |
| `ScalarMunicipalAggregation.py` | Agregado municipio-día compartido |
| `AtmosphericPressureRules.py` | Despacho del contrato de presión |
| `AtmosphericPressureDailyAudit.py` | Despacho de auditoría de presión |
| `WindSpeedRules.py` | Despacho del contrato de viento |
| `WindSpeedDailyAudit.py` | Despacho de auditoría de viento |
| `tests/test_climate_processing.py` | Utilidades y reglas preliminares |
| `tests/test_precipitation_daily_audit.py` | Auditoria diaria |
| `tests/test_precipitation_daily_consolidation.py` | Consolidacion y proteccion del notebook 05 |
| `tests/test_climate_geography.py` | Cruce geografico y proteccion del notebook 06 |
| `tests/test_precipitation_municipal_aggregation.py` | Agregacion municipal y proteccion del notebook 07 |
| `tests/test_precipitation_municipal_audit.py` | Auditoria municipal y proteccion de su notebook |
| `tests/test_temperature_processing.py` | Contratos y despacho de temperatura |
| `tests/test_temperature_daily_audit.py` | Calendario, extremos y sensores de temperatura |
| `tests/test_pending_climate_rules.py` | Bloqueo explicito de variables sin contrato |

## Pipeline agrícola

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `ClimatePipeline/01_2_CropYieldDataDownloader.ipynb` | Descargar EVA Socrata por departamento, año y período | Implementado |
| `ClimatePipeline/02_2_CropYieldDataAudit.ipynb` | Auditar esquema, cobertura, llaves, períodos y medidas crudas | Implementado y ejecutado |
| `ClimatePipeline/09_EvaCurator.ipynb` | Consolidar taxonomías compatibles y recalcular el target | Implementado y ejecutado |
| `ClimatePipeline/09_2_EvaCuratedAudit.ipynb` | Validar llave, fórmula y cobertura del producto curado | Implementado y ejecutado |
| `ClimatePipeline/CropYieldProcessing.py` | Contratos puros de auditoría y curación EVA | Probado |
| `ClimatePipeline/CropYieldAuditRunner.py` | Ejecutar y reanudar las tres etapas agrícolas | Ejecutado |
| `ClimatePipeline/CropMunicipalChange.py` | Agregar por municipio-período y calcular cambios interanuales | Probado |
| `ClimatePipeline/CropMunicipalChangeRunner.py` | Materializar el agregado y auditar su enlace DIVIPOLA | Ejecutado |
| `tests/test_crop_yield_processing.py` | Normalización, banderas, consolidación y compuerta final | Activo |
| `tests/test_crop_municipal_change.py` | Universos por métrica, períodos y geografía | Activo |

Las reglas futuras deben seguir el mismo principio de separacion, no
necesariamente copiar la misma implementacion.

## Pronóstico agrícola

Todo el código predictivo está aislado en `notebooks/CropForecasting/`.

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `CropForecasting/01_Dataset_Definitivo_2026.ipynb` | Construir y auditar el dataset 2019-2026 | Implementado |
| `CropForecasting/02_Entrenamiento_Evaluacion_2026.ipynb` | Backtesting, selección y pronóstico final | Implementado y ejecutado |
| `CropForecasting/03_Graficas_Features_y_Pronostico_2026.ipynb` | Graficar cada feature, categorías y resultado 2026 | Implementado y verificado |
| `CropForecasting/climate.py` | NASA POWER diario, climatología y escenarios as-of | Probado |
| `CropForecasting/dataset.py` | Rezagos, unión y compuertas contra fuga | Probado |
| `CropForecasting/modeling.py` | Modelos, métricas y backtesting expansivo | Probado |
| `CropForecasting/visualization.py` | 45 gráficas numéricas, categorías y paneles finales | Verificado |
| `CropForecasting/RESULTS.md` | Métricas y pronóstico resumido | Vigente |

## Utilidades exploratorias

| Notebook | Uso recomendado | Cautela |
|---|---|---|
| `SocrataProfiler.ipynb` | Consultar esquema, fechas y muestras pequenas de APIs | No descargar datasets masivos |
| `ClimateVariables.ipynb` | Historia de exploracion y primer descargador de precipitacion | Reemplazado operativamente por `ClimatePipeline/01_`; conserva outputs historicos |

## Notebooks heredados por dominio

| Notebook | Dominio | Estado documental |
|---|---|---|
| `CropData.ipynb` | Cultivos, cruces DIVIPOLA y exploracion de rendimiento | Heredado; rutas Drive y orden de ejecucion por revisar |
| `GeoData.ipynb` | DIVIPOLA, comparaciones municipales y geometrias | Heredado; no ejecutar completo sin archivos compartidos y revision |
| `MeteoData.ipynb` | Exploracion meteorologica anterior | Heredado; alcance y salidas por auditar |
| `SoilData.ipynb` | Analisis de laboratorio de suelos | Heredado; fuente, salidas y vigencia por auditar |

Estos notebooks no son la fuente de verdad del pipeline nuevo. Tampoco deben
borrarse hasta identificar datos curados, reglas o visualizaciones que aun no
hayan sido promovidos.

## Presentación y documentación consolidada

| Archivo | Uso |
|---|---|
| `docs/data_pipeline/README.md` | Entrada al ciclo de clima, cultivos, geografía y pronóstico |
| `docs/presentation/RESULTADOS_PROCESO_DATOS_2026.md` | Documento listo para presentación |
| `docs/presentation/generate_presentation_charts.py` | Regenera figuras desde artefactos reales |
| `docs/documentation_review_scrum18.md` | Registro de documentos eliminados, archivados y preservados |

## Donde buscar cada respuesta

| Pregunta | Documento |
|---|---|
| Que esta decidido hoy | `docs/project_status.md` |
| Que sigue y de que depende | `docs/project_roadmap.md` |
| Que archivo produce y consume cada fase | `docs/data_artifacts.md` |
| Cómo funciona cada dominio de punta a punta | `docs/data_pipeline/README.md` |
| Cómo se ejecuta un paso climático | `docs/climate_pipeline_guide.md` |
| Que revelo una corrida | `docs/climate_audits/` y manifiesto en Drive |
| Que fuentes climaticas se eligieron | `docs/data_pipeline/climate.md` y `forecast.md` |
| Que fuente EVA y cultivos tienen cobertura | `docs/data_pipeline/agriculture.md` |
| Que modelo ganó y cuáles son los pronósticos 2026 | `docs/data_pipeline/forecast.md` |
| Qué presentar a una audiencia no técnica | `docs/presentation/RESULTADOS_PROCESO_DATOS_2026.md` |
| Como colaborar con Git y Colab | `CONTRIBUTING.md` |
