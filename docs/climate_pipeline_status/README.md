# Estado del pipeline climatico por variable

**Actualizado:** 29 de julio de 2026
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

| Variable | 01 Crudo | 02 Auditoria | Reglas | 03 Diario sensor | 04 Auditoria diaria | 05 Curado | 06 Geografia | 07 Municipio | 08 Periodo |
|---|---|---|---|---|---|---|---|---|---|
| [Precipitacion](precipitacion.md) | `[P]` | `[X]` | `[X]` | `[X]` | `[X]` | `[X]` | `[X]` | `[P]` | `[ ]` |
| [Temperatura ambiente](temperatura_ambiente.md) | `[P]` | `[X]` | `[P]` | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Temperatura minima](temperatura_minima.md) | `[P]` | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Temperatura maxima](temperatura_maxima.md) | `[P]` | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Humedad](humedad.md) | `[P]` | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Presion atmosferica](presion_atmosferica.md) | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| [Velocidad del viento](velocidad_viento.md) | `[P]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

El estado `[P]` de los crudos significa que las carpetas esperadas fueron
observadas o reportadas, pero falta una reconciliacion de integridad que revise
partes consecutivas, ultimo lote, fechas internas y manifiestos para todo el
alcance.

El estado `[P]` de municipio para precipitacion significa que la agregacion
oficial ya existe, pero su auditoria cientifica de cobertura y sensibilidad
todavia debe ejecutarse y revisarse en Colab.

## Como retomar una variable

Una persona o asistente de IA debe:

1. Leer `project_status.md`, `climate_pipeline_guide.md` y la ficha de esta
   carpeta correspondiente a la variable.
2. Empezar en el primer paso no terminado que la ficha marque como siguiente
   accion. No se salta una compuerta porque exista un notebook posterior.
3. Revisar los manifiestos y reportes enlazados. Una conversacion previa no
   reemplaza evidencia persistida.
4. Si `<Variable>Rules.py` o `<Variable>DailyAudit.py` es un marcador
   bloqueante, completar primero 02, proponer el contrato y agregar pruebas. No
   se elimina el bloqueo para forzar una corrida.
5. Ejecutar un piloto de 03 y 04 para enero-febrero de 2025, ambos
   departamentos, antes de escalar.
6. Disenar y probar la consolidacion 05 propia de la variable. El orden general
   es: piloto 03 -> piloto 04 -> contrato 05 -> escala 03 -> cierre 04 ->
   consolidacion 05 completa.
7. Solo con `clima_diario_curado` completo se adapta y ejecuta 06. Solo con
   geografia canonica se crea la regla variable-especifica de 07.
8. Auditar municipio-dia antes de producir indicadores de 08. Cobertura,
   dispersion, agregaciones e imputacion se deciden por variable.

Los pasos a la derecha del tablero muestran la ruta esperada. No significan que
el codigo ya este implementado para todas las variables.

## Punto de reanudacion actual

| Variable | Siguiente accion exacta | Compuerta que desbloquea |
|---|---|---|
| Precipitacion | Ejecutar `07_2_Climate_Precipitation_MunicipalAudit.ipynb` y revisar Aquitania/Puerto Salgar | Decision de regla municipal y paso 08 |
| Temperatura ambiente | Repetir las cuatro particiones piloto con 03 v2 y ejecutar 04 v2 | Diseno de consolidacion termica 05 |
| Temperatura minima | Verificar crudo 2024 con 02 y ejecutar piloto 03 de enero-febrero de 2025 | Auditoria diaria 04 |
| Temperatura maxima | Verificar crudo 2024, ejecutar piloto 03 y revisar conflictos exportados | Auditoria diaria 04 |
| Humedad | Completar 02 en ambos departamentos y anos | Contrato `HumidityRules.py` |
| Presion atmosferica | Ejecutar 02 sobre meses contrastantes 2024-2025 | Contrato `AtmosphericPressureRules.py` |
| Velocidad del viento | Ejecutar 02 sobre meses contrastantes 2024-2025 | Contrato `WindSpeedRules.py` |

## Regla de actualizacion

1. Actualizar la ficha de la variable despues de una corrida validada.
2. Enlazar el manifiesto, reporte o sintesis que respalda el cambio.
3. Actualizar este tablero solo si cambia el estado de una etapa.
4. Actualizar `project_status.md` si cambia el alcance o una prioridad global.
