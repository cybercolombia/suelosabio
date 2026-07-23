# Procesamiento diario de temperatura

El notebook `03_ClimateDailyProcessor.ipynb` admite tres contratos de
temperatura independientes. Comparte infraestructura de rutas, manifiestos y
escritura con precipitacion, pero no comparte sus reglas semanticas.

## Configuracion de 03

Seleccione una fila completa; no combine el nombre de una variable con el
dataset de otra:

| `VARIABLE_NOMBRE` | `DATASET_ID` | Estadistico principal |
|---|---|---|
| `temperatura_ambiente` | `sbwg-7ju4` | media diaria |
| `temperatura_minima` | `afdg-3zpb` | minimo diario |
| `temperatura_maxima` | `ccvq-rp9s` | maximo diario |

Ejemplo de piloto:

```python
VARIABLE_NOMBRE = 'temperatura_ambiente'
DATASET_ID = 'sbwg-7ju4'
PROCESAR_DEPARTAMENTOS = ['CUNDINAMARCA']
PROCESAR_ANIOS = [2025]
PROCESAR_MESES = [1]
WORKER_ID = 'worker_temperatura_a'
MAX_PARTICIONES = 1
SOBRESCRIBIR_RESULTADOS = False
EJECUTAR_PROCESAMIENTO = False
```

Primero se ejecuta con la bandera en `False` para revisar el plan. Despues se
activa `EJECUTAR_PROCESAMIENTO=True` y se ejecuta solo la ultima celda.

## Salida de 03

La ruta conserva variable, fuente, departamento, ano y mes:

```text
clima_diario_sensor/
  variable=temperatura_ambiente/fuente=sbwg-7ju4/
    departamento=CUNDINAMARCA/anio=2025/mes=01/
      observaciones_diarias.parquet
      cadencias.parquet
      duplicados_eliminados.parquet
      conflictos.parquet
      rechazados.parquet
      resumen_procesamiento.parquet
      manifest.json
```

`observaciones_diarias.parquet` mantiene una fila por estacion, sensor y dia.
Incluye media, mediana, minimo, maximo, desviacion, amplitud, observaciones,
cadencia y cobertura. Los sensores nunca se fusionan en esta etapa.

## Configuracion de 04

Use exactamente la misma variable, fuente, departamentos, anos y meses que
terminaron `COMPLETA` en 03. Para el piloto anterior:

```python
VARIABLE_NOMBRE = 'temperatura_ambiente'
DATASET_ID = 'sbwg-7ju4'
AUDITAR_DEPARTAMENTOS = ['CUNDINAMARCA']
AUDITAR_ANIOS = [2025]
AUDITAR_MESES = [1]
AUDITORIA_NOMBRE = 'piloto_temperatura_ambiente_2025_01'
EJECUTAR_AUDITORIA_DIARIA = False
```

Los umbrales iniciales de -10 °C, 45 °C, 25 °C de amplitud y 1 °C entre
sensores son diagnosticos. Marcan observaciones para revision; no las borran ni
las convierten automaticamente en invalidas.

## Limite actual

El notebook 05 y `PrecipitationDailyConsolidation.py` siguen siendo exclusivos
de precipitacion. No se deben ejecutar para temperatura. El contrato de
consolidacion termica se definira despues de revisar los pilotos exportados por
04.
