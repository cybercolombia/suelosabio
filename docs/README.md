# Mapa de documentacion de RAIZ

Este indice es la puerta de entrada para el equipo y para asistentes de IA. Antes
de proponer codigo, alcance o modelos se debe leer
[`project_status.md`](project_status.md), que es la fuente de verdad sobre el
estado vigente del proyecto.

## Orden de lectura recomendado

1. [`project_status.md`](project_status.md): alcance confirmado, decisiones
   pendientes, datos disponibles y siguiente trabajo.
2. [`climate_pipeline_guide.md`](climate_pipeline_guide.md): operacion,
   compuertas, escalamiento y datos faltantes.
3. [`climate_pipeline_status/README.md`](climate_pipeline_status/README.md):
   checklist de avance por variable.
4. [`project_roadmap.md`](project_roadmap.md): fases, dependencias y compuertas.
5. [`data_artifacts.md`](data_artifacts.md): entradas y salidas persistidas.
6. [`repository_guide.md`](repository_guide.md): mapa de notebooks y modulos.
7. [`climate_data_strategy.md`](climate_data_strategy.md): arquitectura climatica
   y principios metodologicos.
8. El documento operativo de la etapa que se vaya a ejecutar.
9. Las auditorias relacionadas, como evidencia y no como instrucciones vigentes.

## Documentos vigentes

| Documento | Contenido | Uso |
|---|---|---|
| [`project_status.md`](project_status.md) | Estado y alcance actual | Leer siempre primero |
| [`project_roadmap.md`](project_roadmap.md) | Ruta completa hasta aplicacion | Planificacion y dependencias |
| [`data_artifacts.md`](data_artifacts.md) | Productores, consumidores, rutas y estados | Contratos entre fases |
| [`repository_guide.md`](repository_guide.md) | Notebooks, modulos y estado de revision | Navegacion del codigo |
| [`climate_pipeline_guide.md`](climate_pipeline_guide.md) | Pipeline 01-08, compuertas, escala y faltantes | Guia tecnica principal |
| [`climate_pipeline_status/README.md`](climate_pipeline_status/README.md) | Estado paso a paso de cada variable | Seguimiento operativo |
| [`climate_data_strategy.md`](climate_data_strategy.md) | Estrategia y flujo climatico 01-08 | Referencia arquitectonica |
| [`climate_daily_processing.md`](climate_daily_processing.md) | Paso 03 de precipitacion: estacion-sensor-dia | Operacion |
| [`climate_daily_audit.md`](climate_daily_audit.md) | Paso 04 de precipitacion | Operacion y diagnostico |
| [`climate_daily_consolidation.md`](climate_daily_consolidation.md) | Paso 05 de precipitacion: estacion-dia | Contrato validado |
| [`climate_geography_audit.md`](climate_geography_audit.md) | Paso 06: catalogo, asignaciones candidatas y mapa | Operacion y compuerta geografica |
| [`climate_municipal_aggregation.md`](climate_municipal_aggregation.md) | Paso 07: precipitacion municipio-dia | Contrato piloto y operacion |
| [`temperature_daily_processing.md`](temperature_daily_processing.md) | Pasos 03 y 04 de temperatura | Operacion y limites |
| [`climate_audits/README.md`](climate_audits/README.md) | Indice de auditorias exportadas | Navegacion de evidencia |

## Investigacion y catalogos

| Documento | Contenido | Vigencia |
|---|---|---|
| [`climate_dataset_candidates.md`](climate_dataset_candidates.md) | Fuentes climaticas, IDs y utilidad potencial | Catalogo vigente; alcance MVP antiguo |
| [`eva_dataset_research.md`](eva_dataset_research.md) | Fuentes EVA, cobertura y cultivos candidatos | Evidencia vigente; seleccion final pendiente |
| [`climate_audits/`](climate_audits/) | Resultados de corridas y hallazgos por variable | Evidencia historica reproducible |

Las normas de ramas, notebooks y datos compartidos estan en
[`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Regla de autoridad

Cuando dos documentos parezcan contradecirse, se aplica este orden:

1. `project_status.md` para alcance y estado presente.
2. Manifiestos y reportes de corridas para resultados verificables.
3. Documentos operativos de cada etapa para instrucciones de ejecucion.
4. Estrategias, investigaciones y auditorias para contexto.
5. Conversaciones y planes dentro de `local_docs/` solo como archivo privado.

Una recomendacion condicionada por una fecha limite pasada no debe tratarse como
decision vigente. Los cambios de alcance se registran primero en
`project_status.md` y despues se propagan a los documentos tecnicos afectados.

## Convencion minima

Todo documento nuevo que contenga decisiones debe indicar:

- Fecha de actualizacion.
- Estado: vigente, en revision o historico.
- Alcance.
- Evidencia o archivos de entrada.
- Decisiones confirmadas y pendientes.
- Documento que lo reemplaza, si deja de estar vigente.
