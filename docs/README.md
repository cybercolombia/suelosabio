# Mapa de documentación de RAIZ

Este índice organiza la documentación para el equipo y para asistentes de
inteligencia artificial. Antes de proponer código, alcance o modelos se debe
consultar [`project_status.md`](project_status.md), que registra el estado
vigente del proyecto.

## Orden de lectura recomendado

1. [`project_status.md`](project_status.md): alcance confirmado, decisiones
   pendientes, datos disponibles y siguiente trabajo.
2. [`data_pipeline/README.md`](data_pipeline/README.md): ciclo consolidado de
   clima, cultivos, geografía y pronóstico.
3. [`presentation/RESULTADOS_PROCESO_DATOS_2026.md`](presentation/RESULTADOS_PROCESO_DATOS_2026.md):
   resultados, gráficas y mapas para presentación.
4. [`climate_pipeline_guide.md`](climate_pipeline_guide.md): operación,
   compuertas, escalamiento y datos faltantes.
5. [`climate_pipeline_status/README.md`](climate_pipeline_status/README.md):
   checklist de avance por variable.
6. [`climate_multivariable_pipeline.md`](climate_multivariable_pipeline.md):
   contratos y ejecución de temperatura, viento y presión.
7. [`project_roadmap.md`](project_roadmap.md): fases, dependencias y compuertas.
8. [`data_artifacts.md`](data_artifacts.md): entradas y salidas persistidas.
9. [`repository_guide.md`](repository_guide.md): mapa de notebooks y módulos.
10. [`../notebooks/CropForecasting/RESULTS.md`](../notebooks/CropForecasting/RESULTS.md):
    evaluación temporal y pronósticos 2026.
11. Las auditorías relacionadas, como evidencia y no como instrucciones vigentes.

## Documentos vigentes

| Documento | Contenido | Uso |
|---|---|---|
| [`project_status.md`](project_status.md) | Estado y alcance actual | Leer siempre primero |
| [`project_roadmap.md`](project_roadmap.md) | Ruta completa hasta aplicación | Planificación y dependencias |
| [`data_artifacts.md`](data_artifacts.md) | Productores, consumidores, rutas y estados | Contratos entre fases |
| [`repository_guide.md`](repository_guide.md) | Notebooks, módulos y estado de revisión | Navegación del código |
| [`data_pipeline/README.md`](data_pipeline/README.md) | Clima, agricultura, geografía y pronóstico | Entrada técnica consolidada |
| [`presentation/RESULTADOS_PROCESO_DATOS_2026.md`](presentation/RESULTADOS_PROCESO_DATOS_2026.md) | Resultados, gráficas, mapas y métricas | Presentación técnica |
| [`climate_pipeline_guide.md`](climate_pipeline_guide.md) | Pipeline 01-08, compuertas, escala y faltantes | Guía técnica principal |
| [`climate_pipeline_status/README.md`](climate_pipeline_status/README.md) | Estado paso a paso de cada variable | Seguimiento operativo |
| [`climate_multivariable_pipeline.md`](climate_multivariable_pipeline.md) | Contratos por variable, inventario y ejecución 01-07 | Operación multivariable |
| [`climate_geography_audit.md`](climate_geography_audit.md) | Paso 06: catálogo, asignaciones candidatas y mapa | Operación y compuerta geográfica |
| [`climate_municipal_aggregation.md`](climate_municipal_aggregation.md) | Paso 07: precipitación municipio-día | Contrato piloto y operación |
| [`climate_municipal_audit.md`](climate_municipal_audit.md) | Paso 07: cobertura y sensibilidad municipal | Operación y compuerta científica |
| [`crop_yield_pipeline.md`](crop_yield_pipeline.md) | Auditoría cruda, curación y auditoría de la variable objetivo EVA | Operación agrícola |
| [`../notebooks/CropForecasting/RESULTS.md`](../notebooks/CropForecasting/RESULTS.md) | Modelo final, métricas y pronósticos de papa 2026 | Resultado predictivo vigente |
| [`climate_audits/README.md`](climate_audits/README.md) | Índice de auditorías exportadas | Navegación de evidencia |
| [`documentation_review_scrum18.md`](documentation_review_scrum18.md) | Redundancias revisadas y acciones ejecutadas | Registro de decisión SCRUM-18 |
| [`language_review_scrum19.md`](language_review_scrum19.md) | Criterios y alcance de la revisión de lenguaje | Registro de decisión SCRUM-19 |
| [`visualization_review_scrum20.md`](visualization_review_scrum20.md) | Mapas incorporados, fuentes y reglas de lectura | Registro de decisión SCRUM-20 |
| [`releases/1.0.0.md`](releases/1.0.0.md) | Alcance, validación y limitaciones de la primera versión | Notas de Release 1.0.0 |

## Documentación histórica

| Documento | Contenido | Estado |
|---|---|---|
| [`archive/design/climate_data_strategy.md`](archive/design/climate_data_strategy.md) | Diseño exploratorio del pipeline | Archivado |
| [`archive/research/climate_dataset_candidates.md`](archive/research/climate_dataset_candidates.md) | Investigación de fuentes climáticas | Archivado |
| [`archive/research/eva_dataset_research.md`](archive/research/eva_dataset_research.md) | Investigación de fuentes EVA | Archivado |
| `climate_daily_processing.md`, `climate_daily_audit.md`, `climate_daily_consolidation.md`, `temperature_daily_processing.md` | Guías piloto sustituidas | Eliminadas con aprobación del usuario |
| [`climate_audits/`](climate_audits/) | Resultados de corridas y hallazgos | Conservar como evidencia reproducible |

Las normas de ramas, notebooks y datos compartidos están en
[`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Regla de autoridad

Cuando dos documentos parezcan contradecirse, se aplica este orden:

1. `project_status.md` para alcance y estado presente.
2. Manifiestos y reportes de corridas para resultados verificables.
3. Documentos operativos de cada etapa para instrucciones de ejecución.
4. Estrategias, investigaciones y auditorías para contexto.
5. Conversaciones y planes dentro de `local_docs/` solo como archivo privado.

Una recomendación condicionada por una fecha límite pasada no debe tratarse como
decisión vigente. Los cambios de alcance se registran primero en
`project_status.md` y después se propagan a los documentos técnicos afectados.

## Convención mínima

Todo documento nuevo que contenga decisiones debe indicar:

- Fecha de actualización.
- Estado: vigente, en revisión o histórico.
- Alcance.
- Evidencia o archivos de entrada.
- Decisiones confirmadas y pendientes.
- Documento que lo reemplaza, si deja de estar vigente.
