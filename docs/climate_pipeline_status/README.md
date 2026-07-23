# Estado del pipeline climatico por variable

**Actualizado:** 22 de julio de 2026  
**Estado:** vigente  
**Alcance operativo:** Boyaca y Cundinamarca, 2024-2025

Esta carpeta responde **hasta donde ha llegado cada variable**. La explicacion
de como funciona el pipeline y sus compuertas permanece en
[`../climate_pipeline_guide.md`](../climate_pipeline_guide.md).

## Leyenda

- `[X]`: terminado y respaldado por una salida o evidencia revisada.
- `[P]`: parcial o en proceso; no habilita por si solo el paso siguiente a escala.
- `[ ]`: pendiente.

`COMPLETA` en un manifiesto significa que una corrida termino y verifico sus
archivos. No significa que toda la variable, todos los meses o su calidad
cientifica esten aprobados.

## Tablero por variable

| Variable | 01 Crudo | 02 Auditoria | Reglas | 03 Diario sensor | 04 Auditoria diaria | 05 Curado | 06 Municipio |
|---|---|---|---|---|---|---|---|
| [Precipitacion](precipitacion.md) | `[P]` | `[P]` | `[X]` | `[P]` | `[P]` | `[P]` | `[ ]` |
| [Temperatura ambiente](temperatura_ambiente.md) | `[P]` | `[X]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Temperatura minima](temperatura_minima.md) | `[P]` | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Temperatura maxima](temperatura_maxima.md) | `[P]` | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Humedad](humedad.md) | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Presion atmosferica](presion_atmosferica.md) | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Velocidad del viento](velocidad_viento.md) | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

El estado `[P]` de los crudos significa que las carpetas esperadas fueron
observadas o reportadas, pero falta una reconciliacion de integridad que revise
partes consecutivas, ultimo lote, fechas internas y manifiestos para todo el
alcance.

## Regla de actualizacion

1. Actualizar la ficha de la variable despues de una corrida validada.
2. Enlazar el manifiesto, reporte o sintesis que respalda el cambio.
3. Actualizar este tablero solo si cambia el estado de una etapa.
4. Actualizar `project_status.md` si cambia el alcance o una prioridad global.
