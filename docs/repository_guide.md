# Guia del repositorio

**Actualizado:** 29 de julio de 2026
**Estado:** inventario vigente; revision de codigo pendiente

Esta guia orienta a personas y asistentes de IA. Clasifica los archivos por su
funcion actual, pero no garantiza que los notebooks heredados ejecuten de
principio a fin. La futura revision de scripts debe actualizar este documento.

## Pipeline climatico activo

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `ClimatePipeline/01_Climate_Precipitation_DataDownloader.ipynb` | Descargar Socrata por departamento, ano y mes | Activo y generico |
| `ClimatePipeline/02_Climate_Precipitation_DataAudit.ipynb` | Auditar crudos y generar evidencia | Activo y generico |
| `ClimatePipeline/03_Climate_Precipitation_DailyProcessor.ipynb` | Producir estacion-sensor-dia | Precipitacion validada; temperatura en piloto |
| `ClimatePipeline/04_Climate_Precipitation_DailyAudit.ipynb` | Auditar la capa diaria preliminar | Precipitacion validada; temperatura en piloto |
| `ClimatePipeline/05_Climate_Precipitation_DailyConsolidator.ipynb` | Producir estacion-dia canonico | Activo solo para precipitacion |
| `ClimatePipeline/06_Climate_Precipitation_GeographyAudit.ipynb` | Validar estaciones contra DIVIPOLA y poligonos | V3 verificada; 116 asignaciones canonicas |
| `ClimatePipeline/07_Climate_Precipitation_MunicipalAggregator.ipynb` | Producir precipitacion municipio-dia | Corrida oficial completa; revision cientifica pendiente |
| `ClimatePipeline/07_2_Climate_Precipitation_MunicipalAudit.ipynb` | Auditar cobertura y sensibilidad municipio-dia | Implementado; corrida Colab pendiente |

Todos quedan protegidos por banderas `EJECUTAR_*` en `False` dentro de Git. Los
pasos 03-05 dependen de contratos por variable; no se vuelven genericos cambiando
un nombre en configuracion.

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
| `AtmosphericPressureRules.py` | Marcador bloqueante hasta definir reglas de presion |
| `AtmosphericPressureDailyAudit.py` | Marcador bloqueante hasta definir la auditoria diaria de presion |
| `WindSpeedRules.py` | Marcador bloqueante hasta definir reglas de viento |
| `WindSpeedDailyAudit.py` | Marcador bloqueante hasta definir la auditoria diaria de viento |
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

## Componentes planeados

Los nombres son contratos de roadmap, no archivos existentes:

| Componente | Producto esperado |
|---|---|
| `07_Climate_Precipitation_MunicipalAggregator.ipynb` | Clima municipio-dia con cobertura espacial |
| `08_ClimatePeriodFeatures.ipynb` | Indicadores climaticos municipio-periodo |
| `09_EvaCurator.ipynb` | EVA curada y target validado |
| `10_MasterDatasetBuilder.ipynb` | Dataset maestro, diccionario y reporte de cruce |
| `11_ModelingPipeline.ipynb` | EDA, baselines, modelos y evaluacion temporal |
| `12_ArtifactsPublisher.ipynb` | Contrato pequeno para aplicacion y sustentacion |

## Donde buscar cada respuesta

| Pregunta | Documento |
|---|---|
| Que esta decidido hoy | `docs/project_status.md` |
| Que sigue y de que depende | `docs/project_roadmap.md` |
| Que archivo produce y consume cada fase | `docs/data_artifacts.md` |
| Como se ejecuta un paso climatico | Documento `climate_daily_*` correspondiente |
| Que revelo una corrida | `docs/climate_audits/` y manifiesto en Drive |
| Que fuentes climaticas existen | `docs/climate_dataset_candidates.md` |
| Que fuente EVA y cultivos tienen cobertura | `docs/eva_dataset_research.md` |
| Como colaborar con Git y Colab | `CONTRIBUTING.md` |
