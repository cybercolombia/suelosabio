# Revisión documental SCRUM-18

**Fecha:** 30 de julio de 2026
**Estado:** recomendaciones aprobadas y ejecutadas

## Decisión ejecutada

El usuario aprobó retirar cuatro guías operativas sustituidas y ejecutar las
recomendaciones de archivo. Se eliminaron las cuatro guías, se archivaron tres
investigaciones y se actualizaron todos sus enlaces entrantes.

## Criterios aplicados

Un documento se conserva en la ruta principal cuando cumple al menos una de
estas funciones:

- contrato vigente de una fase;
- estado actual respaldado por artefactos;
- evidencia de una auditoría ejecutada;
- diccionario o especificación física;
- guía necesaria para reproducir el pipeline.

Un documento se considera candidato cuando describe un piloto ya superado,
duplica un contrato vigente o registra una investigación que ya produjo una
decisión.

## Documentos nuevos que asumen la función principal

| Documento | Función |
|---|---|
| `docs/data_pipeline/climate.md` | Ciclo completo e individual para cada variable climática |
| `docs/data_pipeline/agriculture.md` | Descarga, auditoría, curación y agregado de cultivos |
| `docs/data_pipeline/geography.md` | Estaciones, DIVIPOLA, polígonos y cruces |
| `docs/data_pipeline/forecast.md` | Dataset, métodos, métricas y resultado 2026 |
| `docs/presentation/RESULTADOS_PROCESO_DATOS_2026.md` | Relato pedagógico con gráficas |

## Guías eliminadas

### 1. `docs/climate_daily_processing.md`

Describe el paso 03 de precipitación con énfasis operativo y piloto. Su contrato
vigente ya está explicado en:

- `docs/data_pipeline/climate.md`;
- `docs/climate_pipeline_guide.md`;
- `docs/climate_pipeline_status/precipitacion.md`;
- `PrecipitationRules.py`.

**Acción:** eliminada después de migrar sus enlaces a la ficha consolidada.

### 2. `docs/climate_daily_audit.md`

Explica el paso 04 de precipitación y encadena instrucciones que ya quedaron
respaldadas por reportes de auditoría y la ficha de estado. Parte de su contenido
presupone el piloto anterior al cierre de 48 particiones.

**Acción:** eliminada; la evidencia detallada permanece en los reportes de
auditoría.

### 3. `docs/climate_daily_consolidation.md`

Es el contrato narrativo inicial del paso 05 de precipitación. La versión v2 y
sus decisiones —cuarentena, ajuste temporal y reconciliación— ya están
consolidadas en la nueva ficha y en el reporte de cierre. Aún recibe cinco
enlaces desde documentos históricos.

**Acción:** eliminada después de cambiar los enlaces al reporte de auditoría de
curado y a `data_pipeline/climate.md`.

### 4. `docs/temperature_daily_processing.md`

Describe el piloto de temperatura ambiente como pendiente de repetición con
regla v2. Ese estado es obsoleto: las seis etapas posteriores ya se ejecutaron
para las 48 particiones y existe capa municipio-día.

**Acción:** eliminada y retirada del índice principal.

## Investigaciones archivadas

| Ubicación actual | Razón | Acción |
|---|---|---|
| `docs/archive/design/climate_data_strategy.md` | Diseño exploratorio previo al pipeline ejecutado | Archivado |
| `docs/archive/research/climate_dataset_candidates.md` | Investigación de fuentes que fundamentó la selección | Archivado |
| `docs/archive/research/eva_dataset_research.md` | Investigación EVA anterior al Excel final | Archivado |

Estos documentos aportan trazabilidad de decisiones, pero no deberían competir
con la ruta vigente de lectura. Sus encabezados y referencias relativas fueron
actualizados para indicar su estado histórico.

## Pilotos y reportes intermedios que deben conservarse

No se recomienda eliminar los archivos bajo `docs/climate_audits/`. Aunque
algunos describen pilotos, constituyen evidencia de cómo se detectaron
duplicados, brechas, cambios de escala y conflictos. Deben quedar fuera de la
ruta ejecutiva, pero disponibles para auditoría.

En particular se conservan:

- auditorías crudas por departamento y año;
- piloto y cierre diario de precipitación;
- piloto de temperatura ambiente;
- cierre de curado;
- auditoría geográfica;
- auditoría municipal;
- alerta transversal de febrero de 2025.

## Documentos que se mantienen vigentes

| Grupo | Documentos |
|---|---|
| Gobierno | `README.md`, `project_status.md`, `project_roadmap.md`, `repository_guide.md` |
| Contratos transversales | `climate_pipeline_guide.md`, `climate_multivariable_pipeline.md`, `data_artifacts.md` |
| Estado por variable | Todo `climate_pipeline_status/` después de actualizar su tablero |
| Agricultura | `crop_yield_pipeline.md` más la ficha consolidada |
| Evidencia | Todo `climate_audits/` |
| Pronóstico | `notebooks/CropForecasting/README.md`, `RESULTS.md` y la ficha consolidada |

Los documentos geográficos y municipales anteriores
(`climate_geography_audit.md`, `climate_municipal_aggregation.md` y
`climate_municipal_audit.md`) se conservan por ahora porque contienen contratos
técnicos y siguen enlazados por las fichas de precipitación. Podrán revisarse en
una segunda ronda después de actualizar esos consumidores.

## Resultado

- Cuatro guías piloto eliminadas.
- Tres investigaciones conservadas en `docs/archive/`.
- Reportes bajo `docs/climate_audits/` preservados íntegramente.
- Enlaces actualizados hacia la documentación consolidada.
- Ningún notebook, dataset de Drive ni artefacto de auditoría eliminado.
