# Roadmap de extremo a extremo de RAIZ

**Actualizado:** 22 de julio de 2026
**Estado:** vigente
**Alcance territorial:** Boyaca y Cundinamarca

Este documento explica el orden del proyecto y sus compuertas de calidad. El
alcance vigente se mantiene en [`project_status.md`](project_status.md) y las
rutas se detallan en [`data_artifacts.md`](data_artifacts.md).

## Flujo completo

```text
alcance y fuentes
  -> datos crudos inmutables
  -> auditoria cruda y contrato por variable
  -> clima diario por estacion-sensor
  -> auditoria diaria
  -> clima diario consolidado por estacion
  -> geografia canonica y clima municipal
  -> indicadores municipio-periodo
  -> EVA curada
  -> dataset maestro
  -> EDA, baseline y modelos
  -> artefactos pequenos
  -> aplicacion y sustentacion
```

Una fase no termina porque una celda haya ejecutado. Debe existir un producto
persistido, una validacion y una entrada utilizable por la siguiente fase.

## Resumen de fases

| Fase | Producto principal | Compuerta | Estado |
|---|---|---|---|
| 0. Alcance | Pregunta, cultivos y variables acordados | El equipo comparte el mismo objetivo | En proceso |
| 1. Inventario | Matriz de disponibilidad | Rutas y periodos sin ambiguedad | Clima parcial |
| 2. Auditoria cruda | Evidencia y contrato candidato | Semantica y calidad defendibles | Precipitacion validada; temperatura en piloto; otras parciales |
| 3. Diario por sensor | `clima_diario_sensor` | Llave y trazabilidad verificadas | Precipitacion validada; temperatura implementada |
| 4. Auditoria diaria | `auditorias_clima_diario` | Cobertura y sensores evaluados | Precipitacion validada; temperatura pendiente de corrida |
| 5. Consolidacion | `clima_diario_curado` | Una fila por estacion-dia con calidad | Piloto precipitacion validado |
| 5.1 Escala operativa | Historia diaria 2024-2025 | Particiones y manifiestos completos | Pendiente |
| 6. Municipio y periodo | Indicadores municipio-periodo | Llaves unicas y cobertura visible | Pendiente |
| 7. Agricultura | EVA curada | Target y granularidad verificadas | Pendiente |
| 8. Integracion | Dataset maestro | Cruce, perdidas y fuga auditados | Pendiente |
| 9. Analitica y modelo | Metricas, predicciones y modelo | Superar o explicar baseline temporal | Pendiente |
| 10. Publicacion | Artefactos versionados | Contrato de consumo validado | Pendiente |
| 11. Aplicacion | Demo y narrativa | No procesa crudos al iniciar | Pendiente |

## Fase 0. Cerrar una pregunta viable

- Escoger uno o dos cultivos usando cobertura EVA y relevancia productiva.
- Escoger variables climaticas por utilidad, cobertura y calidad auditada.
- Decidir si suelo u otras fuentes aportan al alcance o quedan como trabajo futuro.
- Confirmar el periodo publicado por EVA que define el target.
- Definir la ventana comun y una evaluacion temporal.

La salida es una actualizacion de `project_status.md`. Una decision pendiente
permanece escrita como pendiente; ningun integrante o asistente debe inferirla.

## Fases 1 y 2. Inventario y auditoria por variable

El paso 01 descarga y el paso 02 diagnostica. El 02 no corrige datos ni convierte
hallazgos automaticamente en reglas. Para habilitar una variable se confirma:

- Dataset, unidad y significado de `valorobservado`.
- Periodo, departamentos, estaciones y sensores.
- Cadencias reales y cambios de frecuencia.
- Nulos, valores no convertibles, duplicados y conflictos.
- Rangos, patrones sospechosos y estabilidad geografica.
- Regla diaria defendible y versionada.

La salida tecnica es un modulo con pruebas, como `PrecipitationRules.py` o
`TemperatureRules.py`. Temperatura ya tiene contrato para piloto; humedad,
presion y viento todavia necesitan contratos propios antes del 03.

## Fases 3, 4 y 5. Construir clima diario

### Paso 03: estacion-sensor-dia

- Deduplica observaciones exactas y separa conflictos y rechazos.
- Infiere cadencia por estacion-sensor.
- Agrega segun la semantica de la variable.
- Conserva cobertura, procedencia y regla aplicada.

### Paso 04: auditoria diaria

- Construye un calendario explicito y diferencia cero de ausencia.
- Examina cobertura, extremos y continuidad.
- Compara sensores paralelos sin mezclarlos.
- Propone ajustes al contrato diario.

### Paso 05: estacion-dia consolidado

- Aplica el contrato versionado y selecciona sensor con reglas defendibles.
- Conserva desacuerdos y ausencias como `NaN`.
- Registra calidad, motivos, parametros y procedencia.

Los tres pasos forman un ciclo por variable. El piloto de precipitacion no
habilita automaticamente las demas. Temperatura dispone de 03 y 04, pero su
paso 05 permanece pendiente hasta revisar pilotos reales.

## Fase 5.1. Escalar 2024-2025

Se ejecutan 03, 04 y 05 por bloques manejables. Puede paralelizarse siempre
que dos workers no escriban la misma particion. La escala termina cuando:

- Todas las particiones esperadas tienen manifiesto `COMPLETA`.
- No existen llaves duplicadas en la capa final.
- La cobertura se resume por variable, departamento, ano y mes.
- Las cuarentenas y cambios de regla quedan versionados.
- Una repeticion no duplica ni mezcla salidas.

## Fase 6. Geografia, municipio y periodos

```text
estacion-sensor-dia -> estacion-dia -> municipio-dia -> municipio-periodo
```

Primero se construye una tabla canonica estacion-municipio con codigos DANE,
DIVIPOLA y evidencia geografica. Luego se combinan estaciones sin dar mas peso a
las que reportan con mayor frecuencia.

Cada variable produce varias caracteristicas: acumulacion o tendencia,
variabilidad, extremos, persistencia y calidad. Un semestre debe conservar perfil
mensual o bloques inicio-mitad-fin para no esconder la distribucion temporal.

La salida incluye dias esperados, dias observados, cobertura, brecha maxima y
numero de estaciones. No se extrapolan sumas ni se imputan municipios en silencio.

## Fase 7. Curar EVA

- Confirmar archivo, hoja, encabezados y periodo.
- Normalizar codigos DANE como texto.
- Filtrar cultivos acordados y ambos departamentos.
- Revisar desagregacion, estado fisico, ciclo y filas repetidas.
- Consolidar produccion y area solo cuando las categorias sean compatibles.
- Recalcular rendimiento como produccion total / area total.
- Registrar el cambio metodologico reportado desde 2022.
- Excluir produccion y area cosechada de los predictores del rendimiento.

La salida tiene llave agricola unica y reporte de inclusiones, exclusiones y
diferencias frente al rendimiento publicado.

## Fase 8. Dataset maestro

El cruce usa codigo municipal, ano, periodo y cultivo. Valida cardinalidad,
reporta filas antes y despues, lista periodos sin clima y conserva calidad.

- Verde: cobertura y variacion suficientes para modelar.
- Amarilla: reducir alcance de forma explicita.
- Roja: no forzar el modelo; entregar pipeline y diagnostico reproducible.

El dataset maestro es la unica entrada analitica. No se releen crudos para cada
grafica o entrenamiento.

## Fase 9. EDA y modelado

- Separar entrenamiento y prueba por tiempo.
- Comparar contra baselines calculados solo con entrenamiento.
- Comenzar con un modelo lineal regularizado y uno de arboles sencillo.
- Usar MAE como metrica principal, RMSE y R2 como complementarias.
- Reportar por departamento, periodo y cultivo cuando el tamano lo permita.
- Evitar fuga mediante produccion, area o estadisticas calculadas con el futuro.

No superar el baseline sigue siendo un resultado valido si se reporta con rigor.

## Fases 10 y 11. Publicacion y aplicacion

La aplicacion consume artefactos pequenos y versionados. No descarga Socrata, no
abre miles de Parquet, no limpia EVA y no entrena al iniciar.

La entrega explica fuentes, cobertura, reglas, perdidas del cruce, evaluacion,
limitaciones y alcance exacto de las predicciones.

## Trabajo paralelizable

| Frente | Puede avanzar cuando | No debe hacer |
|---|---|---|
| Variables climaticas | Crudos disponibles | Copiar reglas de precipitacion |
| EVA | Archivo compartido disponible | Esperar el cierre de todo clima |
| DIVIPOLA y estaciones | Catalogos disponibles | Alterar crudos para corregir nombres |
| Modelado | Dataset maestro versionado | Entrenar directamente desde crudos |
| Frontend | Contrato preliminar de artefactos | Acoplarse a Drive o Colab |
