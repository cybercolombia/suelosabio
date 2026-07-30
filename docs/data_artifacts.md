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
  -> clima_municipal -> auditorias_clima_municipal -> indicadores_climaticos
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
| Productor | `01_Climate_Precipitation_DataDownloader.ipynb` |
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
| Productor | `02_Climate_Precipitation_DataAudit.ipynb` |
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
| Productor | `03_Climate_Precipitation_DailyProcessor.ipynb` |
| Granularidad | Estacion + sensor + dia |
| Consumidor | Paso 04 |
| Estado | Piloto de precipitacion validado; temperatura implementada sin salida real valida aun |

Los auxiliares explican como se obtuvo cada total y se conservan con la particion.

### 04. Auditoria diaria

```text
auditorias_clima_diario/
  variable=<variable>/fuente=<dataset_id>/auditoria=<nombre>/
    calendario_estacion_sensor.parquet
    resumen_particiones.parquet
    resumen_estacion_sensor.parquet
    catalogo_estacion_sensor.parquet
    actividad_mensual_estacion_sensor.parquet
    ausencias_mes_completo.parquet
    valores_sospechosos.parquet
    comparaciones_sensores.parquet
    resumen_sensores_paralelos.parquet
    AuditoriaDiaria_<variable>_<nombre>.md
    manifest.json
    figures/
```

| Propiedad | Valor |
|---|---|
| Productor | `04_Climate_Precipitation_DailyAudit.ipynb` |
| Granularidad | Calendario estacion-sensor-dia y resumen |
| Consumidores | Paso 05 y revision humana |
| Estado | Precipitacion validada; temperatura implementada y pendiente de corrida; las demas variables tienen bloqueadores explicitos |

El calendario agrega filas `NaN` para ausencias; por eso puede superar el numero
de observaciones sin inventar mediciones.

### 05. Clima diario consolidado

```text
clima_diario_curado/
  variable=<variable>/fuente=<dataset_id>/consolidacion=<version>/
    departamento=<departamento>/anio=<yyyy>/mes=<mm>/
      observaciones_estacion_dia.parquet
    candidatos_sensor.parquet
    sensores_cuarentena.parquet
    ajustes_temporales.parquet
    resumen_calidad.parquet
    ConsolidacionDiaria_<variable>_<version>.md
    manifest.json
    figures/
```

| Propiedad | Valor |
|---|---|
| Productor | `05_Climate_Precipitation_DailyConsolidator.ipynb` |
| Granularidad | Estacion + dia |
| Consumidor | Paso 06 |
| Estado | Precipitacion 2024-2025 v2 completa y reconciliada |

El valor original, valor ajustado, sensor seleccionado, calidad, motivo y regla
viajan juntos. Ausencias, sensores invalidos, cuarentenas y desacuerdos
permanecen en `NaN`; los artefactos anteriores nunca se sobrescriben.

### 06. Geografia auditada y curada

```text
geografia_curada/ejecucion=<version>/
  catalogo_estaciones_climaticas.parquet
  estaciones_municipio_candidato.parquet
  estaciones_revision.parquet
  divipola_municipios.parquet
  resumen_geografico.parquet
  mapa_estaciones.html
  manifest.json

geografia_curada/canonica=<version>/
  estaciones_municipio.parquet
  estaciones_revision.parquet
  estaciones_excluidas.parquet
  divipola_municipios_geometria.parquet
  manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `06_Climate_Precipitation_GeographyAudit.ipynb` |
| Granularidad | Estacion; municipio |
| Consumidor | Paso 07 |
| Estado | V3 verificada: 116 canonicas, 9 revisiones y 1 exclusion |

La primera salida conserva la auditoria historica de candidatos. La segunda
valida 239 poligonos y contiene solamente estaciones con asignacion espacial
canonica; los conflictos permanecen en revision y Bogota D.C. queda en una
tabla de exclusiones. Ambas conservan
codigo DANE, coordenadas, fuente, periodo, metodo y evidencia.

### 07. Clima municipal diario

```text
clima_municipal/
  variable=precipitacion/
    fuente=s54a-sgyg/
      agregacion=precipitacion_municipio_dia_2024_2025_v1/
        departamento=<departamento>/anio=<anio>/mes=<mes>/
          precipitacion_municipio_dia.parquet
        resumen_municipios.parquet
        cobertura_municipal_diaria.html
        AgregacionMunicipal_precipitacion_2024_2025.md
        manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `07_Climate_Precipitation_MunicipalAggregator.ipynb` |
| Granularidad | Municipio + dia |
| Consumidor | Paso 08 |
| Estado | Corrida oficial completa: 48 particiones y 174.709 filas; revision cientifica pendiente |

Conserva estaciones esperadas, observadas y validas, cobertura, dispersion,
calidad y metodo. La mediana no ponderada es el valor piloto; media y extremos
permanecen disponibles. Las estaciones nunca se suman para construir
precipitacion.

### 07.1 Auditoria municipal diaria

```text
auditorias_clima_municipal/
  variable=precipitacion/
    fuente=s54a-sgyg/
      auditoria=cierre_precipitacion_municipal_2024_2025_v1/
        cobertura_municipios.parquet
        cobertura_periodos.parquet
        cobertura_insuficiente.parquet
        multiestacion_dias.parquet
        resumen_multiestacion.parquet
        sensibilidad_media_mediana_anual.parquet
        sensibilidad_umbrales_lluvia.parquet
        *.html
        AuditoriaMunicipal_precipitacion_2024_2025.md
        manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `07_2_Climate_Precipitation_MunicipalAudit.ipynb` |
| Granularidad | Municipio, municipio-periodo y municipio-dia multiestacion |
| Consumidor | Decision humana y paso 08 |
| Estado | Implementado y prevalidado localmente; corrida Colab pendiente |

Es una auditoria de solo lectura. Los acumulados de media y mediana usan los
mismos dias validos y no extrapolan ausencias. Un estado
`COMPLETA_CON_REVISION_PENDIENTE` confirma que la auditoria termino, no que la
regla municipal ya fue aprobada.

### 08. Indicadores climaticos por periodo

```text
indicadores_climaticos/variable=<variable>/municipio_periodo.parquet
indicadores_climaticos/data_dictionary.md
indicadores_climaticos/quality_report.md
indicadores_climaticos/manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | Futuro `08_ClimatePeriodFeatures.ipynb` |
| Granularidad | Municipio + ano + periodo |
| Consumidor | Paso 10 |
| Estado | Planeado |

Conserva dias esperados, observados, cobertura y brecha maxima. Los indicadores
dependen de variable y periodo agricola; no se reducen todos a una media.

### 09. Agricultura curada

```text
auditorias_agricultura/capa=eva_cruda/fuente=<dataset_id>/auditoria=<version>/
  resumen_auditoria.parquet
  nulos_columnas.parquet
  llaves_duplicadas.parquet
  banderas_calidad.parquet
  cobertura_eva.parquet
  manifest.json

agricultura_curada/version=<version>/
  eva_curada.parquet
  exclusiones.parquet
  reconciliacion.parquet
  resumen_cobertura.parquet
  data_dictionary.md
  manifest.json

auditorias_agricultura/capa=eva_curada/auditoria=<version>/
  summary.parquet
  row_checks.parquet
  duplicate_keys.parquet
  coverage.parquet
  manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `02_2_CropYieldDataAudit.ipynb`, `09_EvaCurator.ipynb` y `09_2_EvaCuratedAudit.ipynb` |
| Granularidad | Municipio + ano + periodo + cultivo |
| Consumidor | Paso 10 |
| Estado | Implementado y ejecutado; revisión humana pendiente |

El nombre no incluye papa porque el conjunto puede contener uno o dos cultivos.
Las taxonomias incompatibles se excluyen con motivo trazable. Produccion y area
cosechada se conservan para auditar el target, pero el manifiesto las declara
columnas no predictoras.

### 09.1 Agricultura municipal y cambios

```text
agricultura_municipal/version=cultivo_municipio_periodo_v1/
  cultivo_municipio_periodo.parquet
  cambios_interanuales.parquet
  incidencias_agregacion.parquet
  resumen_agregacion.parquet
  auditoria_geografica.parquet
  diferencias_nombres_divipola.parquet
  manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | `CropMunicipalChangeRunner.py` |
| Granularidad | Municipio + año + período + cultivo; cambios por par de años |
| Consumidor | Mapas agrícolas y paso 10 |
| Estado | Ejecutado: 13.692 targets, 9.377 comparaciones y 239 municipios con geometría |

Las áreas sembrada y cosechada tienen universos de validez independientes del
rendimiento. Las comparaciones emparejan solamente A con A, B con B y anual con
anual. La geometría permanece como dimensión canónica separada y se enlaza por
código DANE, evitando repetir polígonos en cada fila temporal.

### 10. Dataset maestro

```text
dataset_maestro/version=<version>/
  master_dataset.parquet
  data_dictionary.md
  join_report.md
  manifest.json
```

| Propiedad | Valor |
|---|---|
| Productor | Futuro `10_MasterDatasetBuilder.ipynb` |
| Granularidad | Municipio + ano + periodo + cultivo |
| Consumidor | Paso 11 exclusivamente |
| Estado | Planeado |

Conserva procedencia, variables, target, calidad y perdidas del cruce. Produccion
y area auditan el target, pero no son features si rendimiento se calcula con ellas.

### 11. Corridas de modelado

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

### 12. Artefactos para aplicacion

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

El futuro `12_ArtifactsPublisher.ipynb` selecciona una corrida aprobada; no
recalcula el pipeline. La aplicacion consume esta salida sin montar Drive.

## Reglas de trazabilidad

- Los crudos son inmutables.
- Toda salida registra fuente, parametros, regla, commit, inicio y fin.
- La escritura final ocurre despues de validar un temporal legible.
- Una salida incompleta no se mezcla con una corrida nueva.
- Las rutas provisionales se actualizan aqui al implementar su productor.
- Los archivos grandes permanecen en Drive; Git conserva codigo y sintesis.
