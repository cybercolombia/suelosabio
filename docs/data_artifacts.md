# Catalogo de artefactos y dependencias

**Actualizado:** 22 de julio de 2026
**Estado:** vigente

Las rutas de datos corresponden a `eco2026_processed` en Google Drive y no se
agregan a Git. Git conserva codigo, pruebas, contratos y sintesis legibles.

## Estados

| Estado | Significado |
|---|---|
| Disponible | Existe para todo el alcance declarado |
| Piloto | Existe solo para particiones de validacion |
| Parcial | Existe para algunas variables o territorios |
| Planeado | Contrato propuesto; productor aun no implementado |

## Cadena de dependencias

```text
project_status
  -> clima_crudo
  -> auditorias_climaticas + reglas de variable
  -> clima_diario_sensor
  -> auditorias_clima_diario
  -> clima_diario_curado
  -> geografia_curada
  -> clima_municipal -> indicadores_climaticos
  + agricultura_curada
  -> dataset_maestro
  -> model_runs -> artifacts -> aplicacion
```

Un manifiesto `COMPLETA` significa que el productor termino y verifico sus
salidas. No significa que la cobertura cientifica sea suficiente.

## Artefactos por fase

### 01. Clima crudo

```text
clima_crudo/
  variable=<variable>/fuente=<dataset_id>/
    departamento=<departamento>/anio=<yyyy>/mes=<mm>/part-*.parquet
```

| Propiedad | Valor |
|---|---|
| Productor | `01_ClimateDataDownloader.ipynb` |
| Granularidad | Observacion subdiaria por estacion-sensor |
| Consumidores | Pasos 02 y 03 |
| Regla | Inmutable; nunca se corrige en sitio |
| Estado | Disponible estructuralmente 2021-2025 para precipitacion, humedad, presion y viento; temperatura 2024-2025 reportada y parcialmente verificada |

La existencia de las 120 carpetas esperadas por variable no garantiza cobertura
interna, calidad o continuidad.

### 02. Auditoria climatica cruda

```text
auditorias_climaticas/
  variable=<variable>/fuente=<dataset_id>/ejecucion=<etiqueta>/
    *.parquet
    AuditoriaClimatica_<etiqueta>.md
```

| Propiedad | Valor |
|---|---|
| Productor | `02_ClimateDataAudit.ipynb` |
| Granularidad | Resumen por corrida y tablas diagnosticas |
| Consumidores | Reglas, alcance y documentacion |
| Estado | Precipitacion amplia; temperatura 2024-2025 parcial; humedad Cundinamarca 2025; otras pendientes |

Los Parquet completos permanecen en Drive. Las sintesis promovidas a Git viven
en `docs/climate_audits/`.

### Contratos de variable

```text
notebooks/ClimatePipeline/<Variable>Rules.py
tests/test_<variable>_processing.py
```

| Propiedad | Valor |
|---|---|
| Productor | Desarrollo posterior a la auditoria 02 |
| Consumidor | Paso 03 |
| Contenido | Columnas, unidad, deduplicacion, rechazos, cadencia y agregacion diaria |
| Estado | Precipitacion validada; temperatura en piloto; humedad, presion y viento bloqueadas por marcadores explicitos |

Cambiar `VARIABLE_NOMBRE` no habilita una variable sin contrato y pruebas.

### 03. Clima diario por sensor

```text
clima_diario_sensor/
  variable=<variable>/fuente=<dataset_id>/
    departamento=<departamento>/anio=<yyyy>/mes=<mm>/
      observaciones_diarias.parquet
      cadencias.parquet
      duplicados_eliminados.parquet
      conflictos.parquet
      rechazados.parquet
      resumen_procesamiento.parquet
      manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `03_ClimateDailyProcessor.ipynb` |
| Granularidad | Estacion + sensor + dia |
| Consumidor | Paso 03_01 |
| Estado | Piloto de precipitacion validado; temperatura implementada sin salida real valida aun |

Los auxiliares explican como se obtuvo cada total y se conservan con la particion.

### 03_01. Auditoria diaria

```text
auditorias_clima_diario/
  variable=<variable>/fuente=<dataset_id>/auditoria=<nombre>/
    calendario_estacion_sensor.parquet
    resumen_particiones.parquet
    resumen_estacion_sensor.parquet
    valores_sospechosos.parquet
    comparaciones_sensores.parquet
    resumen_sensores_paralelos.parquet
    AuditoriaDiaria_<variable>_<nombre>.md
    manifest.json
    figures/
```

| Propiedad | Valor |
|---|---|
| Productor | `03_01_ClimateDailyAudit.ipynb` |
| Granularidad | Calendario estacion-sensor-dia y resumen |
| Consumidores | Paso 04 y revision humana |
| Estado | Piloto de precipitacion validado; auditor de temperatura implementado y pendiente de corrida |

El calendario agrega filas `NaN` para ausencias; por eso puede superar el numero
de observaciones sin inventar mediciones.

### 04. Clima diario consolidado

```text
clima_diario_curado/
  variable=<variable>/fuente=<dataset_id>/consolidacion=<version>/
    departamento=<departamento>/anio=<yyyy>/mes=<mm>/
      observaciones_estacion_dia.parquet
    candidatos_sensor.parquet
    sensores_cuarentena.parquet
    resumen_calidad.parquet
    ConsolidacionDiaria_<variable>_<version>.md
    manifest.json
    figures/
```

| Propiedad | Valor |
|---|---|
| Productor | `04_ClimateDailyConsolidator.ipynb` |
| Granularidad | Estacion + dia |
| Consumidor | Paso 05 |
| Estado | Piloto de precipitacion validado |

El valor, sensor seleccionado, calidad, motivo y regla viajan juntos. Ausencias,
sensores invalidos y desacuerdos permanecen en `NaN`.

### Geografia curada

```text
geografia_curada/divipola_municipios.parquet
geografia_curada/estaciones_municipio.parquet
```

| Propiedad | Valor |
|---|---|
| Productor | Curacion DIVIPOLA y reglas geograficas por definir |
| Granularidad | Municipio; estacion-periodo |
| Consumidores | Pasos 05, 06 y 07 |
| Estado | Planeado |

Debe conservar codigo DANE, nombres canonicos, coordenadas, fuente, periodo de
validez y evidencia de reasignaciones.

### 05. Clima municipal e indicadores

```text
clima_municipal/variable=<variable>/municipio_dia.parquet
indicadores_climaticos/variable=<variable>/municipio_periodo.parquet
indicadores_climaticos/data_dictionary.md
indicadores_climaticos/quality_report.md
```

| Propiedad | Valor |
|---|---|
| Productor | Futuro `05_ClimateMunicipalAggregator.ipynb` |
| Granularidad | Municipio-dia y municipio-periodo |
| Consumidores | Dataset maestro y EDA climatico |
| Estado | Planeado |

Conserva cobertura, brecha maxima, estaciones y dispersion. Las agregaciones
dependen de variable y periodo agricola; no se reducen todas a una media.

### 06. Agricultura curada

```text
agricultura_curada/eva_curada.parquet
agricultura_curada/data_dictionary.md
agricultura_curada/quality_report.md
```

| Propiedad | Valor |
|---|---|
| Productor | Futuro `06_EvaCurator.ipynb` |
| Granularidad | Municipio + ano + periodo + cultivo |
| Consumidor | Paso 07 |
| Estado | Planeado |

El nombre no incluye papa porque el conjunto puede contener uno o dos cultivos.

### 07. Dataset maestro

```text
dataset_maestro/version=<version>/
  master_dataset.parquet
  data_dictionary.md
  join_report.md
  manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | Futuro `07_MasterDatasetBuilder.ipynb` |
| Granularidad | Municipio + ano + periodo + cultivo |
| Consumidor | Paso 08 exclusivamente |
| Estado | Planeado |

Conserva procedencia, variables, target, calidad y perdidas del cruce. Produccion
y area auditan el target, pero no son features si rendimiento se calcula con ellas.

### 08. Corridas de modelado

```text
model_runs/run=<id>/
  metrics.json
  predictions.parquet
  feature_importance.csv
  figures/
  run_metadata.json
```

Cada corrida registra dataset maestro, corte temporal, baseline, features,
parametros, metricas y commit. Su estado es planeado.

### 09. Artefactos para aplicacion

```text
artifacts/release=<version>/
  model.joblib
  model_metadata.json
  metrics.json
  predictions.parquet
  feature_importance.csv
  summary_by_department.csv
  figures/
```

El futuro `09_ArtifactsPublisher.ipynb` selecciona una corrida aprobada; no
recalcula el pipeline. La aplicacion consume esta salida sin montar Drive.

## Reglas de trazabilidad

- Los crudos son inmutables.
- Toda salida registra fuente, parametros, regla, commit, inicio y fin.
- La escritura final ocurre despues de validar un temporal legible.
- Una salida incompleta no se mezcla con una corrida nueva.
- Las rutas provisionales se actualizan aqui al implementar su productor.
- Los archivos grandes permanecen en Drive; Git conserva codigo y sintesis.
