# Auditorias climaticas

Esta carpeta conserva sintesis legibles de calidad climatica. Los Parquet
detallados permanecen en Drive y los datos de entrada nunca se modifican durante
una auditoria.

## Organizacion por etapa

| Carpeta | Entrada auditada | Productor | Pregunta principal |
|---|---|---|---|
| [`02_datos_crudos/`](02_datos_crudos/) | `clima_crudo` | `02_ClimateDataAudit.ipynb` | La fuente puede transformarse y con que reglas |
| [`04_series_diarias/`](04_series_diarias/) | `clima_diario_sensor` | `04_ClimateDailyAudit.ipynb` | La transformacion produjo una serie diaria defendible |
| [`05_clima_curado/`](05_clima_curado/) | `clima_diario_curado` | Reconciliacion del paso 05 | La capa curada respeta manifiesto, calidad y trazabilidad |
| [`transversales/`](transversales/) | Varias etapas o variables | Sintesis documental | El hallazgo se repite o conecta varios productos |

La numeracion de las carpetas coincide con el paso del pipeline que genera la
auditoria. `transversales` no recibe numero porque sus reportes no pertenecen a
una unica etapa.

## Regla de ubicacion

- Si el reporte lee `part-*.parquet` de `clima_crudo`, va en
  `02_datos_crudos`.
- Si lee `observaciones_diarias.parquet` o calendarios producidos despues del
  paso 03, va en `04_series_diarias`.
- Si verifica `observaciones_estacion_dia.parquet` y auxiliares producidos por
  05, va en `05_clima_curado`.
- Si combina evidencia cruda, diaria o de varias variables, va en
  `transversales`.

Los nombres de archivo deben identificar variable, territorio y periodo. Cada
subcarpeta mantiene su propio indice de reportes.
